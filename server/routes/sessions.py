"""Rotas de sessoes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.deps import get_state
from server.schemas import MessageInfo, SessionCreate, SessionInfo

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionInfo])
async def list_sessions(limit: int = 50) -> list[SessionInfo]:
    state = get_state()
    return [SessionInfo(**s) for s in state.memory.sessions.list(limit=limit)]


@router.post("", response_model=SessionInfo, status_code=201)
async def create_session(payload: SessionCreate) -> SessionInfo:
    state = get_state()
    sid = state.memory.sessions.create(title=payload.title)
    if payload.project_id:
        p = state.memory.projects.resolve(payload.project_id)
        if p is None:
            raise HTTPException(status_code=404, detail=f"projeto '{payload.project_id}' nao encontrado")
        state.memory.projects.link_session(sid, p["id"])

    s = state.memory.sessions.get(sid)
    if s is None:
        raise HTTPException(status_code=500, detail="sessao criada mas nao encontrada")
    return SessionInfo(**s)


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str) -> SessionInfo:
    state = get_state()
    s = state.memory.sessions.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"sessao '{session_id}' nao encontrada")
    return SessionInfo(**s)


@router.get("/{session_id}/messages", response_model=list[MessageInfo])
async def get_messages(session_id: str, limit: int = 200) -> list[MessageInfo]:
    state = get_state()
    s = state.memory.sessions.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"sessao '{session_id}' nao encontrada")
    return [MessageInfo(**m) for m in state.memory.sessions.messages(session_id, limit=limit)]


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str) -> None:
    state = get_state()
    s = state.memory.sessions.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"sessao '{session_id}' nao encontrada")
    # sessions repo nao tem delete explicito; adiciona aqui
    state.memory.store.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    state.memory.store.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    state.memory.projects.unlink_session(session_id)
