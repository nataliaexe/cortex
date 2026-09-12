"""Loop cognitivo do Cortex com suporte a multi-intent.

Fluxo de uma mensagem:
  1. grava percepcao (input do usuario)
  2. detecta multi-intent (IntentSplitter)
  3. se 1 tarefa: roda o fluxo normal (plan + tools + resposta)
  4. se N tarefas: roda cada uma como subtarefa sequencial,
     concatena numa resposta unica
  5. grava resposta final, atualiza working memory, episodic
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from cortex.config import CortexConfig
from cortex.governance.authorizer import Authorizer
from cortex.governance.dry_run import DryRunPreview, format_preview
from cortex.memory.facade import Memory
from cortex.models.local import ChatMessage
from cortex.models.registry import ModelRegistry
from cortex.nucleus.critic import Critic
from cortex.nucleus.intent_splitter import IntentSplitter, SplitResult
<<<<<<< HEAD
=======
from cortex.nucleus.modes import get_mode
>>>>>>> 23a25f8 (semana 1 fechada: multi-provider + tools + governanca + multi-intent + modes + rate tracker)
from cortex.nucleus.planner import Plan, Planner
from cortex.nucleus.router import AllProvidersFailed, Router
from cortex.tools.base import ToolContext, ToolResult
from cortex.tools.registry import get_registry
from cortex.utils.events import Event, get_event_bus
from cortex.utils.logging import get_logger

log = get_logger(__name__)

PLANNING_TASKS = {"code_generation", "code_refactor", "security_analysis", "planning"}


@dataclass(slots=True)
class SubTaskResult:
    objective: str
    final_text: str
    provider: str
    model: str
    plan: Plan | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    dry_runs_pending: list[DryRunPreview] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class TurnResult:
    user_input: str
    final_text: str
    session_id: str
    provider: str
    model: str
    was_multi_intent: bool = False
    subtasks: list[SubTaskResult] = field(default_factory=list)
    plan: Plan | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    dry_runs_pending: list[DryRunPreview] = field(default_factory=list)
    error: str | None = None


class CortexLoop:
    def __init__(
        self,
        cfg: CortexConfig,
        memory: Memory,
        registry: ModelRegistry,
        router: Router,
    ) -> None:
        self.cfg = cfg
        self.memory = memory
        self.registry = registry
        self.router = router
        self.authorizer = Authorizer(memory.store)
        self.critic = Critic(router)
        self.tool_registry = get_registry()
        self.planner = Planner(router, tools_catalogue=self.tool_registry.catalogue())
        self.splitter = IntentSplitter(router)
        self.bus = get_event_bus()

    # ---------- helpers ----------

    async def _emit(self, kind: str, session_id: str, payload: dict[str, Any], **extra: Any) -> Event:
        ev = Event(kind=kind, session_id=session_id, payload=payload, **extra)  # type: ignore[arg-type]
        self.memory.events.append(ev)
        await self.bus.publish(ev)
        return ev

    def _classify_task(self, text: str, has_tools: bool = False) -> str:
        t = text.lower()
        sec_kw = ["vulnerabilidade", "scan", "exploit", "cve", "segurança", "seguranca", "ataque"]
        code_kw = ["codigo", "código", "função", "funcao", "refator", "implemente", "corrija", "bug", "teste"]
        plan_kw = ["planeje", "plano", "passo a passo", "etapas", "estrategia"]

        if any(k in t for k in sec_kw):
            return "security_analysis"
        if any(k in t for k in code_kw):
            return "code_generation"
        if any(k in t for k in plan_kw):
            return "planning"
        if has_tools:
            return "tool_selection"
        return "chat"

    def _should_plan(self, text: str, task: str) -> bool:
        if task in PLANNING_TASKS:
            return True
        t = text.lower()
        import re as _re
        if _re.search(r"(/|~)\S+", text):
            return True
        if _re.search(r"\b\w+\.(py|txt|md|json|yaml|yml|sh|js|ts|html|css|db|csv)\b", t):
            return True
        action_verbs = [
            "liste", "leia", "crie", "edite", "rode", "execute", "analise",
            "gere", "abra", "mostre", "busque", "encontre", "procure",
            "delete", "apague", "remova", "mova", "copie", "renomeie",
        ]
        return any(v in t for v in action_verbs)

    def _build_context(self, session_id: str, window: int = 20) -> str:
        msgs = self.memory.sessions.messages(session_id, limit=window)
        working = self.memory.working.get(session_id)
        parts = []
        if working:
            parts.append(f"[working memory] {json.dumps(working, ensure_ascii=False)}")
        for m in msgs[-window:]:
            parts.append(f"[{m['role']}] {m['content']}")
        return "\n".join(parts)

    def _messages_for_llm(self, session_id: str, system: str, user_text: str) -> list[ChatMessage]:
        msgs = [ChatMessage(role="system", content=system)]
        for m in self.memory.sessions.messages(session_id, limit=self.cfg.memory.working_window_messages):
            if m["role"] in ("user", "assistant"):
                msgs.append(ChatMessage(role=m["role"], content=m["content"]))
        msgs.append(ChatMessage(role="user", content=user_text))
        return msgs

    # ---------- execucao de tool ----------

    async def _execute_tool(
        self,
        session_id: str,
        tool_name: str,
        args: dict[str, Any],
        user_request: str,
        auto_confirm: bool,
    ) -> tuple[ToolResult | None, DryRunPreview | None]:
        tool = self.tool_registry.get(tool_name)
        if tool is None:
            return ToolResult(ok=False, error=f"tool desconhecida: {tool_name}"), None

        auth = self.authorizer.authorize(tool_name, args)
        audit_id = self.authorizer.log_decision(tool_name, args, auth, session_id=session_id)

        await self._emit(
            "decision",
            session_id,
            {"tool": tool_name, "args": args, "decision": auth.decision, "reason": auth.reason},
            policy_decision=auth.decision,
        )

        if auth.decision == "deny":
            result = ToolResult(ok=False, error=f"negado pela governanca: {auth.reason}")
            self.authorizer.update_audit_result(audit_id, "denied")
            return result, None

        if auth.decision == "dry_run" and not auto_confirm:
            preview = tool.preview(args)
            self.authorizer.update_audit_result(audit_id, "dry_run_pending")
            return None, preview

        if tool.destructive:
            verdict = await self.critic.review(
                tool=tool_name,
                args=args,
                context=self._build_context(session_id, window=5),
                user_request=user_request,
            )
            await self._emit(
                "decision",
                session_id,
                {"tool": tool_name, "critic_approved": verdict.approved, "critic_reason": verdict.reason},
            )
            if not verdict.approved:
                result = ToolResult(
                    ok=False,
                    error=f"critic rejeitou: {verdict.reason}"
                    + (f" | sugestao: {verdict.suggestion}" if verdict.suggestion else ""),
                )
                self.authorizer.update_audit_result(audit_id, "critic_rejected")
                return result, None

        ctx = ToolContext(session_id=session_id, memory=self.memory, config=self.cfg)
        try:
            result = tool.run(args, ctx)
        except Exception as e:
            result = ToolResult(ok=False, error=f"excecao na execucao: {type(e).__name__}: {e}")

        await self._emit(
            "tool_result",
            session_id,
            {"tool": tool_name, "ok": result.ok, "output": result.output[:8000], "error": result.error},
        )
        self.authorizer.update_audit_result(audit_id, "ok" if result.ok else f"error: {result.error}")
        return result, None

    # ---------- subtarefa (uma intencao) ----------

    async def _run_single(
        self,
        session_id: str,
        objective: str,
        auto_confirm: bool,
        is_subtask: bool = False,
<<<<<<< HEAD
=======
        mode: str = "default",
>>>>>>> 23a25f8 (semana 1 fechada: multi-provider + tools + governanca + multi-intent + modes + rate tracker)
    ) -> SubTaskResult:
        """Roda uma unica intencao: classifica, planeja, executa, responde."""
        task = self._classify_task(objective)
        should_plan = self._should_plan(objective, task)

        plan: Plan | None = None
        tool_calls: list[dict[str, Any]] = []
        dry_runs: list[DryRunPreview] = []

        if should_plan:
            plan = await self.planner.plan(objective, context=self._build_context(session_id, window=10))
            await self._emit("plan", session_id, plan.to_dict())

            for step in plan.steps:
                if not step.tool:
                    continue
                result, preview = await self._execute_tool(
                    session_id=session_id,
                    tool_name=step.tool,
                    args=step.args,
                    user_request=objective,
                    auto_confirm=auto_confirm,
                )
                if preview is not None:
                    dry_runs.append(preview)
                    step.result = f"(dry-run pendente) {preview.description}"
                    continue
                if result is not None:
                    step.done = result.ok
                    step.result = (result.output or result.error or "")[:8000]
                    tool_calls.append(
                        {
                            "tool": step.tool,
                            "args": step.args,
                            "ok": result.ok,
                            "output": result.output[:8000],
                            "error": result.error,
                        }
                    )
                    self.memory.working.patch(
                        session_id,
                        {"last_tool": step.tool, "last_ok": result.ok},
                    )

<<<<<<< HEAD
        # monta system e mensagens para a resposta final
        system = (
            "Voce e o Cortex, assistente pessoal de Nana. "
            "Responda em portugues do Brasil. Sem emoji. Seja direto e util. "
            "Se faltar informacao, pergunte em vez de inventar.\n\n"
            "REGRAS CRITICAS SOBRE TOOLS:\n"
=======
        # monta system baseado no modo ativo
        active_mode = get_mode(mode)
        system = active_mode.system_prompt
        system += (
            "\n\nREGRAS CRITICAS SOBRE TOOLS:\n"
>>>>>>> 23a25f8 (semana 1 fechada: multi-provider + tools + governanca + multi-intent + modes + rate tracker)
            "- Se uma tool nao executou (dry-run pendente, negada, ou falhou), "
            "diga claramente que a tool nao rodou e por que. NAO invente o resultado.\n"
            "- Se uma tool executou com sucesso, use APENAS o output real dela. "
            "Nunca complete com suposicoes.\n"
            "- Se o output de uma tool parece truncado, diga que esta truncado em vez de "
            "inventar o que vem depois.\n"
            "- Nunca afirme que um arquivo esta vazio, que nao existe, ou que algo "
            "nao funciona, se voce nao confirmou isso com uma tool de verdade."
        )
        if is_subtask:
            system += (
                "\n\nEsta e uma subtarefa de um pedido maior. "
                "Responda apenas esta parte, de forma concisa."
            )
        if plan is not None:
            # em vez de jogar o plano inteiro (que inclui resultados de tool com nomes
            # de arquivo sensiveis), resume so o que foi executado
            summary_lines = []
            for i, s in enumerate(plan.steps, 1):
                status = "ok" if s.done else "pendente"
                summary_lines.append(f"  {i}. {s.description} [{status}]")
                if s.tool and s.result:
                    # so a primeira linha do resultado, para dar contexto ao LLM
                    first_line = s.result.strip().splitlines()[0][:200] if s.result.strip() else ""
                    summary_lines.append(f"     -> {first_line}")
            system += "\n\nPlano executado (resumo):\n" + "\n".join(summary_lines)

        msgs = self._messages_for_llm(session_id, system, objective)

        try:
            route = await self.router.route(task, msgs, temperature=0.4)
            final_text = route.text
            provider = route.provider
            model = route.model
        except AllProvidersFailed as e:
            log.error("loop_all_providers_failed", error=str(e))
            final_text = "Nao consegui gerar resposta: todos os providers falharam."
            provider = "none"
            model = "none"

        await self._emit("response", session_id, {"text": final_text, "objective": objective})
        self.memory.sessions.add_message(session_id, "assistant", final_text)

        return SubTaskResult(
            objective=objective,
            final_text=final_text,
            provider=provider,
            model=model,
            plan=plan,
            tool_calls=tool_calls,
            dry_runs_pending=dry_runs,
        )

    # ---------- turno completo (com multi-intent) ----------

    async def run_turn(
        self,
        session_id: str,
        user_input: str,
        auto_confirm: bool = False,
<<<<<<< HEAD
    ) -> TurnResult:
        await self._emit("perception", session_id, {"text": user_input})
=======
        mode: str = "default",
    ) -> TurnResult:
        await self._emit("perception", session_id, {"text": user_input, "mode": mode})
>>>>>>> 23a25f8 (semana 1 fechada: multi-provider + tools + governanca + multi-intent + modes + rate tracker)
        self.memory.sessions.add_message(session_id, "user", user_input)

        # 1. detecta multi-intent
        split: SplitResult = await self.splitter.split(user_input)

        if split.was_multi:
            await self._emit(
                "decision",
                session_id,
                {
                    "kind": "multi_intent",
                    "tasks": split.tasks,
                    "splitter_provider": split.provider,
                },
            )
            log.info("multi_intent_detected", n=len(split.tasks), tasks=split.tasks)

        # 2. roda cada subtarefa em sequencia
        subtask_results: list[SubTaskResult] = []
        for i, obj in enumerate(split.tasks, 1):
            if split.was_multi:
                await self._emit(
                    "plan",
                    session_id,
                    {"kind": "subtask_start", "index": i, "total": len(split.tasks), "objective": obj},
                )
            sub = await self._run_single(
                session_id,
                obj,
                auto_confirm,
                is_subtask=split.was_multi,
<<<<<<< HEAD
=======
                mode=mode,
>>>>>>> 23a25f8 (semana 1 fechada: multi-provider + tools + governanca + multi-intent + modes + rate tracker)
            )
            subtask_results.append(sub)

        # 3. sintese final
        if not split.was_multi:
            # caminho normal: uma unica resposta
            final = subtask_results[0]
            provider = final.provider
            model = final.model
            final_text = final.final_text
            agg_plan = final.plan
            agg_tools = final.tool_calls
            agg_dry = final.dry_runs_pending
        else:
            # sintetiza N respostas num relatorio unico
            provider = subtask_results[0].provider if subtask_results else "none"
            model = subtask_results[0].model if subtask_results else "none"
            blocks: list[str] = []
            for i, sub in enumerate(subtask_results, 1):
                blocks.append(f"### Tarefa {i}: {sub.objective}\n{sub.final_text}")
            final_text = "\n\n".join(blocks)
            agg_plan = None
            agg_tools = [tc for sub in subtask_results for tc in sub.tool_calls]
            agg_dry = [p for sub in subtask_results for p in sub.dry_runs_pending]
            # registra a resposta agregada
            self.memory.sessions.add_message(session_id, "assistant", final_text)

        # 4. working memory e episodico
        self.memory.working.patch(
            session_id,
            {
                "last_task": subtask_results[-1].objective if subtask_results else user_input,
                "last_provider": provider,
                "last_model": model,
                "last_multi_intent": split.was_multi,
            },
        )
        summary = user_input[:80] + ("..." if len(user_input) > 80 else "")
        self.memory.episodic.add(
            session_id=session_id,
            summary=summary,
            content=final_text[:500],
            tags=(split.tasks if split.was_multi else [self._classify_task(user_input)]),
            importance=0.5 if split.was_multi else 0.4,
        )

        return TurnResult(
            user_input=user_input,
            final_text=final_text,
            session_id=session_id,
            provider=provider,
            model=model,
            was_multi_intent=split.was_multi,
            subtasks=subtask_results,
            plan=agg_plan,
            tool_calls=agg_tools,
            dry_runs_pending=agg_dry,
        )

    async def stream_turn(
        self,
        session_id: str,
        user_input: str,
        auto_confirm: bool = False,
    ) -> AsyncIterator[Event]:
        result = await self.run_turn(session_id, user_input, auto_confirm=auto_confirm)
        chunk_size = 4
        text = result.final_text
        for i in range(0, len(text), chunk_size):
            piece = text[i : i + chunk_size]
            await self.bus.publish(
                Event(kind="token", session_id=session_id, payload={"text": piece})
            )
        return
