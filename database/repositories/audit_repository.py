from __future__ import annotations

from database.connection import Database
from .base import new_id, now, to_json


class AuditRepository:
    def __init__(self, database: Database): self.database = database

    def record(self, action: str, outcome: str, authorization: dict, parameters: dict | None = None) -> str:
        event_id = new_id()
        with self.database.connection() as conn:
            conn.execute("INSERT INTO audit_events (id, action, outcome, authorization_json, parameters_json, created_at) VALUES (?, ?, ?, ?, ?, ?)", (event_id, action, outcome, to_json(authorization), to_json(parameters or {}), now()))
        return event_id

    def recent(self, limit: int = 100) -> list[dict]:
        with self.database.connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,))]
