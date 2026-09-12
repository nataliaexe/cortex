"""Memoria de trabalho: estado curto da sessao atual."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from cortex.memory.store import Store


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkingMemory:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get(self, session_id: str) -> dict[str, Any]:
        row = self.store.query_one(
            "SELECT state FROM working WHERE session_id = ?", (session_id,)
        )
        if row is None:
            return {}
        return json.loads(row["state"])

    def set(self, session_id: str, state: dict[str, Any]) -> None:
        now = _utc_now()
        existing = self.store.query_one(
            "SELECT session_id FROM working WHERE session_id = ?", (session_id,)
        )
        payload = json.dumps(state, ensure_ascii=False)
        if existing is None:
            self.store.execute(
                "INSERT INTO working (session_id, state, updated_at) VALUES (?, ?, ?)",
                (session_id, payload, now),
            )
        else:
            self.store.execute(
                "UPDATE working SET state = ?, updated_at = ? WHERE session_id = ?",
                (payload, now, session_id),
            )

    def patch(self, session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        current = self.get(session_id)
        current.update(updates)
        self.set(session_id, current)
        return current

    def clear(self, session_id: str) -> None:
        self.store.execute("DELETE FROM working WHERE session_id = ?", (session_id,))
