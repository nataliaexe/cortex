"""Rotas de chat. /chat (JSON) e /chat/stream (SSE)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from server.deps import get_state
from server.schemas import ChatRequest, ChatResponse
from cortex.utils.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _resolve_or_create_session(session_id: str | None, project_id: str | None) -> str:
    """Se session_id dado, valida; senao cria novo. Liga ao projeto se passado."""
    state = get_state()

    if session_id:
        s = state.memory.sessions.get(session_id)
        if s is None:
            raise HTTPException(status_code=404, detail=f"sessao '{session_id}' nao encontrada")
        sid = session_id
    else:
        sid = state.memory.sessions.create(title="api-chat")

    # liga/religa projeto se passado
    if project_id:
        p = state.memory.projects.resolve(project_id)
        if p is None:
            raise HTTPException(status_code=404, detail=f"projeto '{project_id}' nao encontrado")
        state.memory.projects.link_session(sid, p["id"])

    return sid


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Chat em modo nao-streaming. Retorna a resposta completa de uma vez."""
    state = get_state()
    sid = _resolve_or_create_session(payload.session_id, payload.project_id)

    try:
        result = await state.loop.run_turn(
            session_id=sid,
            user_input=payload.message,
            auto_confirm=payload.auto_confirm,
            mode=payload.mode,
        )
    except Exception as e:
        log.error("chat_failed", error=str(e), session_id=sid)
        raise HTTPException(status_code=500, detail=f"erro no turno: {type(e).__name__}: {e}")

    # serializa tool_calls
    tool_calls = [
        {
            "tool": tc.get("tool"),
            "args": tc.get("args"),
            "ok": tc.get("ok"),
            "output": (tc.get("output") or "")[:2000],
            "error": tc.get("error"),
        }
        for tc in result.tool_calls
    ]
    dry_runs = [
        {
            "tool": p.tool,
            "description": p.description,
            "impact": p.impact,
        }
        for p in result.dry_runs_pending
    ]

    return ChatResponse(
        session_id=sid,
        text=result.final_text,
        provider=result.provider,
        model=result.model,
        was_multi_intent=result.was_multi_intent,
        tool_calls=tool_calls,
        dry_runs_pending=dry_runs,
    )


def _sse(event: str, data: dict[str, Any]) -> str:
    """Formata um evento SSE."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    """Chat em modo streaming via SSE.

    Eventos emitidos:
      - session: id da sessao (logo no comeco)
      - plan: plano gerado (se houver)
      - decision: decisao de governanca por tool
      - tool_call: tool vai executar
      - tool_result: resultado da tool
      - token: pedaco de resposta
      - done: resposta completa + metadados
      - error: erro
    """
    state = get_state()
    sid = _resolve_or_create_session(payload.session_id, payload.project_id)

    async def event_stream() -> AsyncIterator[str]:
        yield _sse("session", {"session_id": sid})

        # intercepta eventos do barramento durante o turno
        # (por simplicidade, roda o turno e depois emite os eventos
        #  mais importantes; streaming real de tokens sera adicionado
        #  quando o loop suportar nativamente)

        queue: asyncio.Queue = asyncio.Queue()

        async def consume_bus():
            """Escuta o event bus e enfileira os eventos da sessao."""
            bus = state.loop.bus
            try:
                async for ev in bus.subscribe():
                    if ev.session_id != sid:
                        continue
                    try:
                        queue.put_nowait(ev)
                    except asyncio.QueueFull:
                        pass
            except Exception:
                pass

        consumer_task = asyncio.create_task(consume_bus())

        # roda o turno em paralelo
        async def run_turn():
            try:
                return await state.loop.run_turn(
                    session_id=sid,
                    user_input=payload.message,
                    auto_confirm=payload.auto_confirm,
                    mode=payload.mode,
                )
            except Exception as e:
                return e

        turn_task = asyncio.create_task(run_turn())

        # consome eventos enquanto o turno roda
        try:
            while not turn_task.done() or not queue.empty():
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=0.2)
                except asyncio.TimeoutError:
                    continue

                kind = ev.kind
                pl = ev.payload or {}

                if kind == "plan":
                    # plan tem steps
                    steps = [
                        {"description": s.get("description"), "tool": s.get("tool"), "done": s.get("done", False)}
                        for s in (pl.get("steps") or [])
                    ]
                    yield _sse("plan", {"steps": steps, "goal": pl.get("goal")})

                elif kind == "decision":
                    yield _sse("decision", pl)

                elif kind == "tool_result":
                    yield _sse("tool_result", {
                        "tool": pl.get("tool"),
                        "ok": pl.get("ok"),
                        "output": (pl.get("output") or "")[:2000],
                        "error": pl.get("error"),
                    })

                elif kind == "token":
                    yield _sse("token", {"text": pl.get("text", "")})

                elif kind == "response":
                    # ignora; a resposta final vai no `done`
                    pass

        finally:
            consumer_task.cancel()
            try:
                await consumer_task
            except (asyncio.CancelledError, Exception):
                pass

        # espera o turno terminar (garantido)
        try:
            result = await turn_task
        except Exception as e:
            yield _sse("error", {"message": f"{type(e).__name__}: {e}"})
            return

        if isinstance(result, Exception):
            yield _sse("error", {"message": f"{type(result).__name__}: {result}"})
            return

        # evento final com resposta completa
        tool_calls = [
            {
                "tool": tc.get("tool"),
                "args": tc.get("args"),
                "ok": tc.get("ok"),
                "output": (tc.get("output") or "")[:2000],
                "error": tc.get("error"),
            }
            for tc in result.tool_calls
        ]
        dry_runs = [
            {"tool": p.tool, "description": p.description, "impact": p.impact}
            for p in result.dry_runs_pending
        ]

        yield _sse("done", {
            "session_id": sid,
            "text": result.final_text,
            "provider": result.provider,
            "model": result.model,
            "was_multi_intent": result.was_multi_intent,
            "tool_calls": tool_calls,
            "dry_runs_pending": dry_runs,
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
