"""Cliente Ollama para modelos locais.

Usa o SDK oficial do ollama. Chat e embeddings num unico ponto.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator

import ollama

from cortex.config import LocalModelConfig
from cortex.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class LocalClient:
    """Cliente fino sobre ollama. Async-friendly."""

    def __init__(self, cfg: LocalModelConfig) -> None:
        self.cfg = cfg
        self.client = ollama.AsyncClient(host=cfg.host)

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        options: dict[str, Any] | None = None,
    ) -> str:
        model_name = model or self.cfg.model
        payload_options = {"temperature": temperature}
        if options:
            payload_options.update(options)

        try:
            response = await self.client.chat(
                model=model_name,
                messages=[m.to_dict() for m in messages],
                options=payload_options,
            )
        except Exception as e:
            log.error("local_chat_failed", model=model_name, error=str(e))
            raise

        return response["message"]["content"]

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        model_name = model or self.cfg.model
        payload_options = {"temperature": temperature}
        if options:
            payload_options.update(options)

        try:
            stream = await self.client.chat(
                model=model_name,
                messages=[m.to_dict() for m in messages],
                options=payload_options,
                stream=True,
            )
        except Exception as e:
            log.error("local_chat_stream_failed", model=model_name, error=str(e))
            raise

        async for chunk in stream:
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                yield piece

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        model_name = model or self.cfg.embed_model
        try:
            response = await self.client.embeddings(model=model_name, prompt=text)
        except Exception as e:
            log.error("local_embed_failed", model=model_name, error=str(e))
            raise
        return response["embedding"]

    async def list_models(self) -> list[str]:
        try:
            result = await self.client.list()
        except Exception as e:
            log.error("local_list_failed", error=str(e))
            return []
        models = result.get("models", [])
        return [m.get("name") or m.get("model") or "" for m in models]

    async def health(self) -> bool:
        try:
            models = await self.list_models()
            return self.cfg.model in models or any(
                self.cfg.model.split(":")[0] in m for m in models
            )
        except Exception:
            return False
