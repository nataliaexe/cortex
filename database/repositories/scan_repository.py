from __future__ import annotations

from database.connection import Database
from .base import new_id, now, to_json


class ScanRepository:
    def __init__(self, database: Database): self.database = database

    def record(self, target: str, scan_type: str, result: dict) -> str:
        scan_id = new_id(); timestamp = now()
        with self.database.connection() as conn:
            conn.execute("INSERT INTO security_scans (id, target, scan_type, status, summary_json, created_at, completed_at) VALUES (?, ?, ?, 'completed', ?, ?, ?)", (scan_id, target, scan_type, to_json(result), timestamp, timestamp))
        return scan_id
