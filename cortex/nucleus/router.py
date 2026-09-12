"""Roteador de modelos. Decide qual provider/modelo usar por tarefa.

Fluxo:
  1. Recebe uma tarefa (chat, code_generation, etc) + mensagens
  2. Checa privacidade: se o payload casar com never_send, forca local
  3. Pega a cadeia de providers da tarefa no router.yaml
  4. Tenta em ordem, com fallback automatico
  5. Registra cada tentativa no audit/usage
"""

from __future__ import annotations

import os

import re
from dataclasses import dataclass, field
from typing import Any

from cortex.config import CortexConfig, RouterConfig, load_router_config
from cortex.models.local import ChatMessage
from cortex.models.registry import ModelRegistry
from cortex.models.remote import RemoteAuthError, RemoteRateLimitError
from cortex.nucleus.rate_tracker import get_rate_tracker
from cortex.utils.logging import get_logger

log = get_logger(__name__)


class AllProvidersFailed(Exception):
    """Todos os providers da cadeia falharam."""

    def __init__(self, task: str, attempts: list["RouteAttempt"]) -> None:
        self.task = task
        self.attempts = attempts
        details = "\n".join(
            f"  - {a.provider}: {a.error}" for a in attempts if a.error
        )
        super().__init__(f"todos os providers falharam para tarefa '{task}':\n{details}")


@dataclass(slots=True)
class RouteAttempt:
    provider: str
    model: str
    ok: bool
    error: str | None = None
    latency_ms: int = 0


@dataclass(slots=True)
class RouteResult:
    text: str
    provider: str
    model: str
    task: str
    attempts: list[RouteAttempt] = field(default_factory=list)
    forced_local_by_privacy: bool = False


class PrivacyGuard:
    """Decide se um payload pode sair para provider remoto."""

    def __init__(self, cfg: RouterConfig) -> None:
        self.patterns = cfg.never_send_patterns
        self.regexes = [re.compile(p) for p in cfg.never_send_regex]

    def is_sensitive(self, text: str) -> tuple[bool, str | None]:
        """Retorna (sensiveis?, motivo)."""
        for pat in self.patterns:
            if self._glob_match(text, pat):
                return True, f"casa com padrao proibido: {pat}"
        for rx in self.regexes:
            if rx.search(text):
                return True, f"casa com regex proibida: {rx.pattern}"
        return False, None

    @staticmethod
    def _glob_match(text: str, pattern: str) -> bool:
        # padrao simples: *.ext ou nome exato
        if pattern.startswith("*."):
            ext = pattern[1:]  # ".key"
            return ext in text
        return pattern in text


class Router:
    """Roteador de tarefas para providers."""

    def __init__(
        self,
        cfg: CortexConfig,
        registry: ModelRegistry,
        router_cfg: RouterConfig | None = None,
    ) -> None:
        self.cfg = cfg
        self.registry = registry
        self.router_cfg = router_cfg or load_router_config()
        self.privacy = PrivacyGuard(self.router_cfg)
        self.rate_tracker = get_rate_tracker()

    def chain_for(self, task: str) -> list[str]:
        """Retorna a cadeia de providers para uma tarefa."""
        chain = self.router_cfg.tasks.get(task)
        if not chain:
            log.warning("no_chain_for_task", task=task, fallback="local")
            return ["local"]
        return list(chain)

    def model_for(self, provider: str, task: str) -> str | None:
        """Retorna override de modelo se houver, senao None (usa default)."""
        overrides = self.router_cfg.model_overrides.get(provider) or {}
        return overrides.get(task)

    async def route(
        self,
        task: str,
        messages: list[ChatMessage],
        force_local: bool = False,
        **kwargs: Any,
    ) -> RouteResult:
        """Executa a tarefa pelo primeiro provider que responder.

        Se force_local=True ou privacidade detectar dado sensivel, ignora remotos.
        """
        chain = self.chain_for(task)
        attempts: list[RouteAttempt] = []

        # privacidade
        forced_local = force_local
        privacy_reason: str | None = None
        if not forced_local:
            full_text = "\n".join(m.content for m in messages)
            is_sensitive, reason = self.privacy.is_sensitive(full_text)
            if is_sensitive:
                forced_local = True
                privacy_reason = reason
                log.info("privacy_forced_local", task=task, reason=reason)

        if forced_local:
            # tenta so local, exceto se o usuario desabilitou
            if os.environ.get("CORTEX_DISABLE_LOCAL") == "1":
                log.warning("privacy_forced_local_but_local_disabled")
                raise AllProvidersFailed(
                    task,
                    [RouteAttempt(provider="local", model="?", ok=False, error="local desabilitado por CORTEX_DISABLE_LOCAL=1")],
                )
            chain = ["local"]

        # filtro global: remove local da cadeia se desabilitado
        if os.environ.get("CORTEX_DISABLE_LOCAL") == "1":
            chain = [p for p in chain if p != "local"] or ["local"]

        for provider in chain:
            # pula provider em cooldown de rate limit recente
            if provider != "local" and self.rate_tracker.is_in_cooldown(provider):
                rem = self.rate_tracker.remaining(provider)
                log.info("route_skip_cooldown", provider=provider, remaining_s=rem)
                attempts.append(
                    RouteAttempt(
                        provider=provider,
                        model="(cooldown)",
                        ok=False,
                        error=f"em cooldown por rate limit ({rem}s restantes)",
                    )
                )
                continue

            model_name = self.model_for(provider, task)

            # se provider desabilitado/sem chave, pula rapido
            if provider != "local":
                client = self.registry.remote(provider)
                if client is None:
                    reason = self.registry._errors.get(provider, "indisponivel")
                    attempts.append(
                        RouteAttempt(provider=provider, model=model_name or "?", ok=False, error=reason)
                    )
                    continue

            import time
            t0 = time.monotonic()
            try:
                text = await self.registry.chat_with(
                    provider, messages, model=model_name, **kwargs
                )
                latency = int((time.monotonic() - t0) * 1000)
                attempts.append(
                    RouteAttempt(
                        provider=provider,
                        model=model_name or "default",
                        ok=True,
                        latency_ms=latency,
                    )
                )
                return RouteResult(
                    text=text,
                    provider=provider,
                    model=model_name or "default",
                    task=task,
                    attempts=attempts,
                    forced_local_by_privacy=forced_local and privacy_reason is not None,
                )
            except RemoteRateLimitError as e:
                latency = int((time.monotonic() - t0) * 1000)
                attempts.append(
                    RouteAttempt(provider=provider, model=model_name or "?", ok=False, error=f"rate limit: {e}", latency_ms=latency)
                )
                log.warning("route_rate_limit", provider=provider, task=task)
                self.rate_tracker.mark_cooldown(provider)
                continue
            except RemoteAuthError as e:
                attempts.append(
                    RouteAttempt(provider=provider, model=model_name or "?", ok=False, error=f"auth: {e}")
                )
                continue
            except Exception as e:
                latency = int((time.monotonic() - t0) * 1000)
                attempts.append(
                    RouteAttempt(
                        provider=provider,
                        model=model_name or "?",
                        ok=False,
                        error=f"{type(e).__name__}: {str(e)[:120]}",
                        latency_ms=latency,
                    )
                )
                log.warning("route_provider_failed", provider=provider, task=task, error=str(e)[:120])
                continue

        raise AllProvidersFailed(task, attempts)
