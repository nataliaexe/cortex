"""Memoria episodica: resumos do que aconteceu, por sessao."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from cortex.memory.store import Store


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EpisodicMemory:
    def __init__(self, store: Store) -> None:
        self.store = store

    def add(
        self,
        session_id: str,
        summary: str,
        content: str,
        tags: list[str] | None = None,
        importance: float = 0.5,
    ) -> str:
        eid = str(uuid.uuid4())
        self.store.execute(
            """
            INSERT INTO episodic (id, session_id, ts, summary, content, tags, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (eid, session_id, _utc_now(), summary, content, ",".join(tags or []), importance),
        )
        return eid

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM episodic ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in rows]

    def by_session(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM episodic WHERE session_id = ? ORDER BY ts DESC LIMIT ?",
            (session_id, limit),
        )
        return [dict(r) for r in rows]
