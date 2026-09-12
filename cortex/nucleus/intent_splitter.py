"""Detector e separador de multi-intent.

Recebe uma mensagem crua e devolve uma lista de sub-objetivos.
Se a mensagem tem so uma intencao, devolve lista com 1 item.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from cortex.models.local import ChatMessage
from cortex.nucleus.router import AllProvidersFailed, Router
from cortex.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class SplitResult:
    tasks: list[str]
    was_multi: bool
    provider: str = ""
    model: str = ""


SPLITTER_SYSTEM = """Voce e o detector de multi-intent do Cortex.

Sua tarefa: analisar a mensagem do usuario e decidir se ela contem
UMA ou VARIAS tarefas independentes.

Regras:
- Se for uma coisa so, retorne lista com 1 item.
- Se forem varias tarefas claras (ex: "liste X e leia Y", "rode os testes; depois me mostre o git status"),
  retorne cada uma como item separado, mantendo os termos originais.
- Nao invente tarefas. Nao junte coisas que sao um passo de outra.
- Mantenha o texto o mais fiel possivel ao original. Nao reescreva demais.
- Maximo 5 tarefas.

Responda SEMPRE em JSON valido:
{"tasks": ["tarefa 1", "tarefa 2", ...]}

Sem texto fora do JSON.

Exemplos:
"liste os arquivos" -> {"tasks": ["liste os arquivos"]}
"liste os arquivos e leia o pyproject.toml" -> {"tasks": ["liste os arquivos", "leia o pyproject.toml"]}
"qual a capital da franca? e a populacao?" -> {"tasks": ["qual a capital da franca?", "qual a populacao da franca?"]}
"rode os testes; depois mostre o git status" -> {"tasks": ["rode os testes", "mostre o git status"]}
"""


# heuristica de fallback quando o LLM nao responde bem
_SPLIT_TOKENS = [
    r"\s+e\s+depois\s+", r"\s+depois\s+", r"\s+em seguida\s+",
    r"\s+e\s+tambem\s+", r"\s+por fim\s+",
    r"\s*;\s*", r"\s*\.\s+(?=[a-z])",
    r"\s+e\s+(?:leia|liste|rode|abra|mostre|busque|encontre|procure|analise|crie|gere|edite|delete|apague|mova|copie)\s+",
]


def _heuristic_split(text: str) -> list[str]:
    """Fallback: divide por padroes comuns de sequencia."""
    parts: list[str] = [text]
    for pat in _SPLIT_TOKENS:
        new_parts: list[str] = []
        for p in parts:
            new_parts.extend(re.split(pat, p, flags=re.IGNORECASE))
        parts = new_parts

    # limpa, remove vazios, tira pontuacao orfa
    cleaned: list[str] = []
    for p in parts:
        s = p.strip().strip(".,;:")
        if s and len(s) >= 3:
            cleaned.append(s)

    # se sobraram menos que o original, mas 1 item, mantem
    if not cleaned:
        return [text]
    return cleaned[:5]


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    return None


class IntentSplitter:
    def __init__(self, router: Router) -> None:
        self.router = router

    async def split(self, text: str) -> SplitResult:
        """Decide se a mensagem tem 1 ou mais intencoes."""
        text = text.strip()
        if not text:
            return SplitResult(tasks=[], was_multi=False)

        # pre-check rapido: se for muito curta, nao chama LLM
        if len(text) < 25:
            return SplitResult(tasks=[text], was_multi=False)

        # se nao tem nenhum separador comum, tambem nao chama LLM
        has_sep = any(
            re.search(pat, text, flags=re.IGNORECASE) for pat in _SPLIT_TOKENS
        )
        if not has_sep:
            return SplitResult(tasks=[text], was_multi=False)

        # chama LLM rapido para separar
        messages = [
            ChatMessage(role="system", content=SPLITTER_SYSTEM),
            ChatMessage(role="user", content=text),
        ]

        try:
            result = await self.router.route("classification", messages, temperature=0.1)
        except AllProvidersFailed as e:
            log.warning("splitter_llm_failed", error=str(e))
            tasks = _heuristic_split(text)
            return SplitResult(tasks=tasks, was_multi=len(tasks) > 1, provider="fallback")

        data = _extract_json(result.text) or {}
        tasks_raw = data.get("tasks") or []

        tasks: list[str] = []
        for t in tasks_raw[:5]:
            if isinstance(t, str) and t.strip():
                tasks.append(t.strip())

        if not tasks:
            tasks = _heuristic_split(text)

        return SplitResult(
            tasks=tasks,
            was_multi=len(tasks) > 1,
            provider=result.provider,
            model=result.model,
        )
