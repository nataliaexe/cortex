"""Armazenamento SQLite unico do Cortex.

Uma so base. Todas as tabelas. WAL para concorrencia leitura/escrita.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

from cortex.utils.logging import get_logger

log = get_logger(__name__)

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    session_id TEXT NOT NULL,
    model_used TEXT,
    policy_decision TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_session_ts ON events(session_id, ts);
CREATE INDEX IF NOT EXISTS idx_events_kind_ts ON events(kind, ts);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    title TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_session_created
    ON messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS episodic (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    importance REAL DEFAULT 0.5,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_episodic_ts ON episodic(ts DESC);

CREATE TABLE IF NOT EXISTS semantic (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,
    confidence REAL DEFAULT 0.7,
    updated_at TEXT NOT NULL,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_semantic_key ON semantic(key);

CREATE TABLE IF NOT EXISTS working (
    session_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    result TEXT,
    session_id TEXT,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit(ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_tool ON audit(tool);

CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    ref_kind TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    model TEXT NOT NULL,
    dim INTEGER NOT NULL,
    vector BLOB NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embeddings_ref ON embeddings(ref_kind, ref_id);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS project_sources (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    ref TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    content TEXT,
    indexed_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sources_project ON project_sources(project_id);
CREATE INDEX IF NOT EXISTS idx_sources_kind ON project_sources(kind);

CREATE TABLE IF NOT EXISTS project_sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_proj_sessions ON project_sessions(project_id);

CREATE TABLE IF NOT EXISTS timers (
    id TEXT PRIMARY KEY,
    label TEXT,
    fire_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    fired INTEGER DEFAULT 0,
    cancelled INTEGER DEFAULT 0,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_timers_fire ON timers(fire_at, fired, cancelled);

CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    fire_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    fired INTEGER DEFAULT 0,
    cancelled INTEGER DEFAULT 0,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_reminders_fire ON reminders(fire_at, fired, cancelled);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_notes_project ON notes(project_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    all_day INTEGER DEFAULT 0,
    source TEXT DEFAULT 'local',
    external_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_calendar_start ON calendar_events(start_at);
CREATE INDEX IF NOT EXISTS idx_calendar_external ON calendar_events(source, external_id);

CREATE TABLE IF NOT EXISTS usage (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    task TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    session_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts DESC);
CREATE INDEX IF NOT EXISTS idx_usage_provider ON usage(provider, ts DESC);
"""


class Store:
    """Wrapper fino sobre sqlite3. Conexao por instancia, WAL ativo."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                isolation_level=None,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: Iterable[Any] | dict[str, Any] = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, seq: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, seq)

    def query(self, sql: str, params: Iterable[Any] | dict[str, Any] = ()) -> list[sqlite3.Row]:
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    def query_one(
        self, sql: str, params: Iterable[Any] | dict[str, Any] = ()
    ) -> sqlite3.Row | None:
        cur = self.conn.execute(sql, params)
        return cur.fetchone()
