"""Repositorio de projetos.

Um projeto agrupa fontes, sessoes e memoria isolada.
Toda operacao passa por aqui.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from cortex.memory.store import Store
from cortex.utils.logging import get_logger

log = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectAlreadyExists(Exception):
    pass


class ProjectNotFound(Exception):
    pass


class ProjectsRepo:
    """CRUD de projetos e vinculos com sessoes."""

    def __init__(self, store: Store) -> None:
        self.store = store

    # ---------- projetos ----------

    def create(
        self,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        name = name.strip()
        if not name:
            raise ValueError("nome do projeto nao pode ser vazio")

        existing = self.store.query_one(
            "SELECT id FROM projects WHERE name = ?", (name,)
        )
        if existing:
            raise ProjectAlreadyExists(f"projeto '{name}' ja existe")

        pid = str(uuid.uuid4())
        now = _utc_now()
        self.store.execute(
            """
            INSERT INTO projects (id, name, description, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (pid, name, description, now, now, json.dumps(metadata or {}, ensure_ascii=False)),
        )
        log.info("project_created", project_id=pid, name=name)
        return pid

    def get(self, project_id: str) -> dict[str, Any] | None:
        row = self.store.query_one("SELECT * FROM projects WHERE id = ?", (project_id,))
        return self._row_to_project(row) if row else None

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        row = self.store.query_one("SELECT * FROM projects WHERE name = ?", (name,))
        return self._row_to_project(row) if row else None

    def resolve(self, ref: str) -> dict[str, Any] | None:
        """Aceita id (uuid) ou nome. Retorna o projeto ou None."""
        # tenta por id
        p = self.get(ref)
        if p:
            return p
        # tenta por nome
        return self.get_by_name(ref)

    def require(self, ref: str) -> dict[str, Any]:
        p = self.resolve(ref)
        if p is None:
            raise ProjectNotFound(f"projeto '{ref}' nao encontrado")
        return p

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        return [self._row_to_project(r) for r in rows]

    def touch(self, project_id: str) -> None:
        self.store.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (_utc_now(), project_id),
        )

    def update(
        self,
        project_id: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        p = self.get(project_id)
        if p is None:
            raise ProjectNotFound(f"projeto '{project_id}' nao encontrado")

        new_desc = description if description is not None else p["description"]
        new_meta = metadata if metadata is not None else p["metadata"]
        self.store.execute(
            "UPDATE projects SET description = ?, metadata = ?, updated_at = ? WHERE id = ?",
            (new_desc, json.dumps(new_meta, ensure_ascii=False), _utc_now(), project_id),
        )

    def delete(self, project_id: str) -> bool:
        cur = self.store.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cur.rowcount > 0

    # ---------- sessoes ligadas ----------

    def link_session(self, session_id: str, project_id: str) -> None:
        # verifica que o projeto existe
        if self.get(project_id) is None:
            raise ProjectNotFound(f"projeto '{project_id}' nao encontrado")
        existing = self.store.query_one(
            "SELECT session_id FROM project_sessions WHERE session_id = ?", (session_id,)
        )
        if existing:
            self.store.execute(
                "UPDATE project_sessions SET project_id = ?, linked_at = ? WHERE session_id = ?",
                (project_id, _utc_now(), session_id),
            )
        else:
            self.store.execute(
                "INSERT INTO project_sessions (session_id, project_id, linked_at) VALUES (?, ?, ?)",
                (session_id, project_id, _utc_now()),
            )

    def unlink_session(self, session_id: str) -> None:
        self.store.execute(
            "DELETE FROM project_sessions WHERE session_id = ?", (session_id,)
        )

    def project_for_session(self, session_id: str) -> dict[str, Any] | None:
        row = self.store.query_one(
            "SELECT project_id FROM project_sessions WHERE session_id = ?", (session_id,)
        )
        if row is None:
            return None
        return self.get(row["project_id"])

    def sessions_for_project(self, project_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.store.query(
            """
            SELECT s.id, s.created_at, s.updated_at, s.title, s.metadata
            FROM sessions s
            JOIN project_sessions ps ON ps.session_id = s.id
            WHERE ps.project_id = ?
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (project_id, limit),
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

    # ---------- helpers ----------

    @staticmethod
    def _row_to_project(r) -> dict[str, Any]:
        return {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "metadata": json.loads(r["metadata"] or "{}"),
        }
