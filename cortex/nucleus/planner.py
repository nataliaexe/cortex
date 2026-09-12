"""Planner. Decompoe uma tarefa em passos executaveis.

O plano e uma lista de passos. Cada passo tem: descricao, tool sugerida (ou null),
args sugeridos (ou {}). O loop cognitivo usa isso para orquestrar.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from cortex.models.local import ChatMessage
from cortex.nucleus.router import AllProvidersFailed, Router
from cortex.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class PlanStep:
    description: str
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    done: bool = False
    result: str | None = None


@dataclass(slots=True)
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "provider": self.provider,
            "model": self.model,
            "steps": [
                {
                    "description": s.description,
                    "tool": s.tool,
                    "args": s.args,
                    "done": s.done,
                    "result": s.result,
                }
                for s in self.steps
            ],
        }


PLANNER_SYSTEM = """Voce e o planner do Cortex.

Sua funcao: decompor a tarefa do usuario em passos concretos e executaveis.

Regras:
- Cada passo deve ser uma acao clara e verificavel.
- Se o passo precisar de uma ferramenta, indique o nome exato em "tool".
- Os argumentos de "args" DEVEM seguir o schema da ferramenta escolhida.
- Se a ferramenta precisar de um argumento obrigatorio e voce nao tem o valor,
  NAO escolha essa ferramenta. Prefira tool=null e descreva em texto.
- Pesquisa: use research.web para perguntas factuais diretas ("o que e X", "quem foi Y").
  Use research.deep APENAS quando o usuario pedir "pesquisa aprofundada", "revisao",
  "estudo sobre", ou quando o tema for amplo e exigir multiplas fontes.
- Se o passo for apenas raciocinio ou resposta final, tool = null, args = {{}}.
- Responda SEMPRE em JSON valido, sem texto fora do JSON.

Ferramentas disponiveis (com schema):
{tools}

Formato obrigatorio:
{{
  "goal": "objetivo resumido em uma linha",
  "steps": [
    {{"description": "o que fazer", "tool": "nome.da.tool" | null, "args": {{...}}}},
    ...
  ]
}}

Maximo 8 passos. Se a tarefa for simples, use 1 passo."""


def _extract_json(text: str) -> dict[str, Any] | None:
    """Extrai JSON de uma resposta que pode ter texto em volta."""
    text = text.strip()
    # tenta direto
    try:
        return json.loads(text)
    except Exception:
        pass
    # tenta entre ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # tenta primeiro { ate ultimo }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    return None


class Planner:
    def __init__(self, router: Router, tools_catalogue: list[dict[str, Any]] | None = None) -> None:
        self.router = router
        self.tools_catalogue = tools_catalogue or []

    async def plan(self, goal: str, context: str = "") -> Plan:
        """Gera um plano para atingir o objetivo."""
        if not self.tools_catalogue:
            tools_text = "(nenhuma ferramenta disponivel)"
        else:
            import json as _json
            lines = []
            for t in self.tools_catalogue:
                lines.append(f"- {t['name']}: {t['description']}")
                lines.append(f"  args schema: {_json.dumps(t.get('schema', {}), ensure_ascii=False)}")
            tools_text = "\n".join(lines)
        system = PLANNER_SYSTEM.format(tools=tools_text)

        user_parts = [f"Objetivo: {goal}"]
        if context:
            user_parts.append(f"Contexto:\n{context}")
        user_parts.append("Gere o plano em JSON.")

        messages = [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content="\n\n".join(user_parts)),
        ]

        try:
            result = await self.router.route("planning", messages, temperature=0.3)
        except AllProvidersFailed as e:
            log.error("planner_failed", error=str(e))
            # fallback: um unico passo com o objetivo
            return Plan(
                goal=goal,
                steps=[PlanStep(description=goal, tool=None, args={})],
                provider="fallback",
                model="none",
                raw="",
            )

        data = _extract_json(result.text) or {}
        steps_raw = data.get("steps") or []
        steps: list[PlanStep] = []
        for s in steps_raw[:8]:
            if not isinstance(s, dict):
                continue
            steps.append(
                PlanStep(
                    description=str(s.get("description", "")).strip() or "(sem descricao)",
                    tool=s.get("tool") or None,
                    args=s.get("args") or {},
                )
            )

        # deduplica steps identicos (mesma tool + mesmos args)
        if steps:
            seen: set[tuple[str | None, str]] = set()
            unique: list[PlanStep] = []
            import json as _json
            for s in steps:
                key = (s.tool, _json.dumps(s.args, sort_keys=True, ensure_ascii=False))
                if key in seen:
                    continue
                seen.add(key)
                unique.append(s)
            steps = unique

        if not steps:
            steps = [PlanStep(description=goal, tool=None, args={})]

        return Plan(
            goal=str(data.get("goal", goal)),
            steps=steps,
            provider=result.provider,
            model=result.model,
            raw=result.text,
        )
