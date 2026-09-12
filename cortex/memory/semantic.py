"""Memoria semantica: fatos consolidados sobre o usuario e seus projetos."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from cortex.memory.store import Store


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SemanticMemory:
    def __init__(self, store: Store) -> None:
        self.store = store

    def upsert(
        self,
        key: str,
        value: str,
        source: str | None = None,
        confidence: float = 0.7,
    ) -> None:
        existing = self.store.query_one("SELECT id FROM semantic WHERE key = ?", (key,))
        now = _utc_now()
        if existing is None:
            self.store.execute(
                "INSERT INTO semantic (id, key, value, source, confidence, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), key, value, source, confidence, now),
            )
        else:
            self.store.execute(
                "UPDATE semantic SET value = ?, source = ?, confidence = ?, updated_at = ? WHERE key = ?",
                (value, source, confidence, now, key),
            )

    def get(self, key: str) -> str | None:
        row = self.store.query_one("SELECT value FROM semantic WHERE key = ?", (key,))
        return row["value"] if row else None

    def all(self, limit: int = 500) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM semantic ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in rows]

    def search_prefix(self, prefix: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM semantic WHERE key LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (f"{prefix}%", limit),
        )
        return [dict(r) for r in rows]

    def delete(self, key: str) -> bool:
        cur = self.store.execute("DELETE FROM semantic WHERE key = ?", (key,))
        return cur.rowcount > 0
