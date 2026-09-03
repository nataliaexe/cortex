"""SQLite connection and schema migration entry point.

The database is persistent local relational storage. Retention is a policy set
by the application; it is not a property of SQLite.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        migration = Path(__file__).parent / "migrations" / "001_initial.sql"
        with self.connection() as conn:
            conn.executescript(migration.read_text(encoding="utf-8"))

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def database_from_config(config: dict) -> Database:
    settings = config.get("database", {})
    return Database(settings.get("path", "data/cortex.db"))
