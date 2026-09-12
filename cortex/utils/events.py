"""Barramento de eventos do Cortex.

Todo perception, decision, tool_call, tool_result e response vira evento.
Eventos sao persistidos em SQLite e tambem publicados em um canal em memoria
para consumidores em tempo real (CLI, SSE, websocket).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Literal

EventKind = Literal[
    "session_start",
    "session_end",
    "perception",
    "decision",
    "plan",
    "tool_call",
    "tool_result",
    "token",
    "response",
    "reflection",
    "error",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Event:
    kind: EventKind
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = field(default_factory=_utc_now_iso)
    model_used: str | None = None
    policy_decision: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class EventBus:
    """Barramento in-process com fila por assinante."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[Event]] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        async with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> AsyncIterator[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=1024)
        async with self._lock:
            self._subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)


_global_bus = EventBus()


def get_event_bus() -> EventBus:
    return _global_bus
