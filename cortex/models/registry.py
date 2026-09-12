"""Pool de providers. Resolve por nome, cuida de cache e disponibilidade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cortex.config import CortexConfig, ProviderConfig
from cortex.models.local import ChatMessage, LocalClient
from cortex.models.remote import RemoteAuthError, RemoteClient
from cortex.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class ProviderStatus:
    name: str
    enabled: bool
    available: bool
    reason: str = ""


class ModelRegistry:
    """Pool de providers + local."""

    def __init__(self, cfg: CortexConfig) -> None:
        self.cfg = cfg
        self._local: LocalClient | None = None
        self._remotes: dict[str, RemoteClient | None] = {}
        self._errors: dict[str, str] = {}
        self._init_remotes()

    def _init_remotes(self) -> None:
        for name, pcfg in self.cfg.providers.items():
            if not pcfg.enabled:
                self._remotes[name] = None
                self._errors[name] = "desabilitado no config"
                continue
            try:
                self._remotes[name] = RemoteClient(name, pcfg)
            except RemoteAuthError as e:
                self._remotes[name] = None
                self._errors[name] = str(e)
                log.warning("provider_unavailable", provider=name, reason=str(e))

    # ---- local ----

    def local(self) -> LocalClient:
        if self._local is None:
            self._local = LocalClient(self.cfg.models.local)
        return self._local

    # ---- remoto ----

    def remote(self, name: str) -> RemoteClient | None:
        return self._remotes.get(name)

    def provider_config(self, name: str) -> ProviderConfig | None:
        return self.cfg.providers.get(name)

    def status(self) -> list[ProviderStatus]:
        result = [
            ProviderStatus(
                name="local",
                enabled=True,
                available=True,
                reason="ollama",
            )
        ]
        for name, pcfg in self.cfg.providers.items():
            client = self._remotes.get(name)
            result.append(
                ProviderStatus(
                    name=name,
                    enabled=pcfg.enabled,
                    available=client is not None,
                    reason=self._errors.get(name, "") if client is None else "ok",
                )
            )
        return result

    def available_providers(self) -> list[str]:
        return [s.name for s in self.status() if s.available]

    # ---- execucao ----

    async def chat_with(
        self,
        provider_name: str,
        messages: list[ChatMessage],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Executa em um provider especifico. Levanta excecao se nao disponivel."""
        if provider_name == "local":
            return await self.local().chat(messages, **kwargs)

        client = self.remote(provider_name)
        if client is None:
            raise RuntimeError(
                f"provider '{provider_name}' indisponivel: "
                f"{self._errors.get(provider_name, 'sem chave')}"
            )
        return await client.chat(messages, model=model, **kwargs)

    async def close(self) -> None:
        for client in self._remotes.values():
            if client is not None:
                try:
                    await client.aclose()
                except Exception:
                    pass
        self._remotes = {k: None for k in self._remotes}
