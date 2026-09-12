"""Sessoes e mensagens."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from cortex.memory.store import Store


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionsRepo:
    def __init__(self, store: Store) -> None:
        self.store = store

    def create(self, title: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        sid = str(uuid.uuid4())
        now = _utc_now()
        self.store.execute(
            "INSERT INTO sessions (id, created_at, updated_at, title, metadata) VALUES (?, ?, ?, ?, ?)",
            (sid, now, now, title, json.dumps(metadata or {}, ensure_ascii=False)),
        )
        return sid

    def touch(self, session_id: str) -> None:
        self.store.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (_utc_now(), session_id),
        )

    def get(self, session_id: str) -> dict[str, Any] | None:
        row = self.store.query_one("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if row is None:
            return None
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "title": row["title"],
            "metadata": json.loads(row["metadata"] or "{}"),
        }

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        return [
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "title": r["title"],
                "metadata": json.loads(r["metadata"] or "{}"),
            }
            for r in rows
        ]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        mid = str(uuid.uuid4())
        now = _utc_now()
        self.store.execute(
            "INSERT INTO messages (id, session_id, role, content, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (mid, session_id, role, content, now, json.dumps(metadata or {}, ensure_ascii=False)),
        )
        self.touch(session_id)
        return mid

    def messages(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT id, role, content, created_at, metadata
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (session_id, limit),
        )
        return [
            {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"],
                "metadata": json.loads(r["metadata"] or "{}"),
            }
            for r in rows
        ]
