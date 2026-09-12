"""Leitura da trilha de auditoria. Append-only feito pelo authorizer."""

from __future__ import annotations

import json
from typing import Any

from cortex.memory.store import Store


class Auditor:
    def __init__(self, store: Store) -> None:
        self.store = store

    def tail(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT id, ts, tool, args, decision, reason, result, session_id
            FROM audit
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row(r) for r in rows]

    def by_tool(self, tool: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT id, ts, tool, args, decision, reason, result, session_id
            FROM audit
            WHERE tool = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (tool, limit),
        )
        return [self._row(r) for r in rows]

    def by_decision(self, decision: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT id, ts, tool, args, decision, reason, result, session_id
            FROM audit
            WHERE decision = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (decision, limit),
        )
        return [self._row(r) for r in rows]

    def denied(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.by_decision("deny", limit)

    def dry_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.by_decision("dry_run", limit)

    @staticmethod
    def _row(r) -> dict[str, Any]:
        return {
            "id": r["id"],
            "ts": r["ts"],
            "tool": r["tool"],
            "args": json.loads(r["args"]) if r["args"] else {},
            "decision": r["decision"],
            "reason": r["reason"],
            "result": r["result"],
            "session_id": r["session_id"],
        }
