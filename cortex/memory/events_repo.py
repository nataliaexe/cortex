"""Persistencia e leitura de eventos."""

from __future__ import annotations

import json
from typing import Any

from cortex.memory.store import Store
from cortex.utils.events import Event


class EventsRepo:
    def __init__(self, store: Store) -> None:
        self.store = store

    def append(self, event: Event) -> None:
        self.store.execute(
            """
            INSERT INTO events (id, ts, kind, session_id, model_used, policy_decision, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.ts,
                event.kind,
                event.session_id,
                event.model_used,
                event.policy_decision,
                json.dumps(event.payload, ensure_ascii=False),
            ),
        )

    def by_session(self, session_id: str, limit: int = 500) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT id, ts, kind, session_id, model_used, policy_decision, payload
            FROM events
            WHERE session_id = ?
            ORDER BY ts ASC
            LIMIT ?
            """,
            (session_id, limit),
        )
        return [self._row_to_dict(r) for r in rows]

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT id, ts, kind, session_id, model_used, policy_decision, payload
            FROM events
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(r) -> dict[str, Any]:
        return {
            "id": r["id"],
            "ts": r["ts"],
            "kind": r["kind"],
            "session_id": r["session_id"],
            "model_used": r["model_used"],
            "policy_decision": r["policy_decision"],
            "payload": json.loads(r["payload"]),
        }
