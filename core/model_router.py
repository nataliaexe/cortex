"""Selects a local model profile before an LLM request is made.

Routing is deterministic and deliberately separate from tool execution: a
model can interpret a request, but it never receives a callable executor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelSelection:
    profile: str
    model: str
    max_tokens: int


class ModelRouter:
    CODING_WORDS = ("código", "code", "python", "javascript", "teste", "bug", "git", "refator", "função", "api")
    REASONING_WORDS = ("planeje", "planejamento", "analise profundamente", "passo a passo", "arquitetura", "ameaça", "vulnerabilidade", "decisão", "estratégia")

    def __init__(self, config: dict[str, Any]):
        llm = config.get("llm", {})
        configured = llm.get("models", {})
        # Accept the former string format so existing local configs keep working.
        self.profiles = {
            "fast": self._profile(configured.get("fast"), configured.get("coding"), "qwen2.5-coder:7b", 180),
            "coding": self._profile(configured.get("coding"), None, "qwen2.5-coder:7b", 500),
            "reasoning": self._profile(configured.get("reasoning"), None, "deepseek-r1:7b", 900),
        }

    @staticmethod
    def _profile(value: Any, fallback: Any, default_name: str, default_tokens: int) -> dict:
        if isinstance(value, dict): return {"name": value.get("name", default_name), "max_tokens": value.get("max_tokens", default_tokens)}
        if isinstance(value, str): return {"name": value, "max_tokens": default_tokens}
        if isinstance(fallback, dict): return {"name": fallback.get("name", default_name), "max_tokens": fallback.get("max_tokens", default_tokens)}
        if isinstance(fallback, str): return {"name": fallback, "max_tokens": default_tokens}
        return {"name": default_name, "max_tokens": default_tokens}

    def select(self, text: str, context: dict[str, Any] | None = None) -> ModelSelection:
        context = context or {}
        requested = context.get("model_profile")
        profile = requested if requested in self.profiles else self._classify(text)
        settings = self.profiles[profile]
        return ModelSelection(profile, settings["name"], int(settings["max_tokens"]))

    def _classify(self, text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in self.REASONING_WORDS): return "reasoning"
        if any(word in lowered for word in self.CODING_WORDS): return "coding"
        return "fast"
