"""Cliente remoto generico para qualquer provider OpenAI-compativel.

Cobre DeepSeek, Groq, Gemini (endpoint /openai), OpenRouter, OpenAI.
Cada provider so difere em base_url, api_key, headers extras e timeout.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from cortex.config import ProviderConfig
from cortex.models.local import ChatMessage
from cortex.utils.logging import get_logger

log = get_logger(__name__)


class RemoteAuthError(Exception):
    """API key ausente ou invalida."""


class RemoteRateLimitError(Exception):
    """Provider retornou 429."""


@dataclass(slots=True)
class RemoteUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class RemoteClient:
    """Cliente generico OpenAI-compatible."""

    def __init__(self, name: str, cfg: ProviderConfig) -> None:
        self.name = name
        self.cfg = cfg
        api_key = os.environ.get(cfg.api_key_env)
        if not api_key:
            raise RemoteAuthError(
                f"API key ausente para provider '{name}' (env: {cfg.api_key_env})"
            )
        self.api_key = api_key

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        for k, v in (cfg.extra_headers or {}).items():
            headers[k] = v

        self._client = httpx.AsyncClient(
            base_url=cfg.base_url.rstrip("/"),
            timeout=httpx.Timeout(cfg.timeout_seconds, connect=15.0),
            headers=headers,
        )
        self.last_usage = RemoteUsage()

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        model_name = model or self.cfg.default_model
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "stream": False,
            # alguns modelos (gpt-oss, qwen coder) tentam chamar tool nativo
            # mesmo sem a gente passar tools. Forcamos modo texto puro.
            "tool_choice": "none",
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format

        try:
            response = await self._client.post("/chat/completions", json=payload)
            if response.status_code == 429:
                raise RemoteRateLimitError(f"{self.name}: rate limit 429")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error(
                "remote_chat_http_error",
                provider=self.name,
                status=e.response.status_code,
                body=e.response.text[:300],
            )
            raise
        except httpx.HTTPError as e:
            log.error("remote_chat_transport_error", provider=self.name, error=str(e))
            raise

        data = response.json()
        usage = data.get("usage", {}) or {}
        self.last_usage = RemoteUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        model_name = model or self.cfg.default_model
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with self._client.stream(
            "POST", "/chat/completions", json=payload
        ) as response:
            if response.status_code == 429:
                raise RemoteRateLimitError(f"{self.name}: rate limit 429")
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                chunk = line[len("data: "):].strip()
                if chunk == "[DONE]":
                    break
                try:
                    data = json.loads(chunk)
                except Exception:
                    continue
                delta = data.get("choices", [{}])[0].get("delta", {})
                piece = delta.get("content")
                if piece:
                    yield piece
