"""Motor de embeddings. Armazena vetores e faz busca por similaridade.

Backend: SQLite puro com armazenamento de vetor como BLOB (float32).
Nao depende de sqlite-vec nesta versao — faz a busca por similaridade
em Python (cosseno). Para projetos pessoais com poucas centenas de
fontes, e rapido o suficiente. Se virar gargalo, troca por sqlite-vec.
"""

from __future__ import annotations

import math
import struct
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cortex.memory.store import Store
from cortex.utils.logging import get_logger

log = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pack_vector(vector: list[float]) -> bytes:
    """Empacota lista de floats como bytes (float32 little-endian)."""
    return struct.pack(f"<{len(vector)}f", *vector)


def _unpack_vector(blob: bytes) -> list[float]:
    """Desempacota bytes para lista de floats."""
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob))


def _cosine(a: list[float], b: list[float]) -> float:
    """Similaridade de cosseno entre dois vetores."""
    if len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


@dataclass(slots=True)
class EmbeddingRecord:
    id: str
    ref_kind: str
    ref_id: str
    model: str
    dim: int
    vector: list[float]
    created_at: str


@dataclass(slots=True)
class SearchHit:
    ref_kind: str
    ref_id: str
    score: float
    payload: dict[str, Any]


class EmbeddingStore:
    """Armazena e busca embeddings por similaridade."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def put(
        self,
        ref_kind: str,
        ref_id: str,
        vector: list[float],
        model: str,
    ) -> str:
        """Guarda um embedding. Se ja existir para (ref_kind, ref_id), substitui."""
        existing = self.store.query_one(
            "SELECT id FROM embeddings WHERE ref_kind = ? AND ref_id = ?",
            (ref_kind, ref_id),
        )
        blob = _pack_vector(vector)
        dim = len(vector)
        now = _utc_now()

        if existing:
            self.store.execute(
                "UPDATE embeddings SET model = ?, dim = ?, vector = ?, created_at = ? WHERE id = ?",
                (model, dim, blob, now, existing["id"]),
            )
            return existing["id"]

        eid = str(uuid.uuid4())
        self.store.execute(
            """
            INSERT INTO embeddings (id, ref_kind, ref_id, model, dim, vector, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (eid, ref_kind, ref_id, model, dim, blob, now),
        )
        return eid

    def delete(self, ref_kind: str, ref_id: str) -> int:
        cur = self.store.execute(
            "DELETE FROM embeddings WHERE ref_kind = ? AND ref_id = ?",
            (ref_kind, ref_id),
        )
        return cur.rowcount

    def get(self, ref_kind: str, ref_id: str) -> EmbeddingRecord | None:
        row = self.store.query_one(
            "SELECT * FROM embeddings WHERE ref_kind = ? AND ref_id = ?",
            (ref_kind, ref_id),
        )
        if row is None:
            return None
        return EmbeddingRecord(
            id=row["id"],
            ref_kind=row["ref_kind"],
            ref_id=row["ref_id"],
            model=row["model"],
            dim=row["dim"],
            vector=_unpack_vector(row["vector"]),
            created_at=row["created_at"],
        )

    def search(
        self,
        query_vector: list[float],
        ref_kind: str | None = None,
        ref_ids: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[SearchHit]:
        """Busca por similaridade de cosseno.

        Filtros:
          - ref_kind: limita a um tipo de referencia ("project_source", "episodic", etc)
          - ref_ids: limita aos ref_ids especificos
        """
        sql = "SELECT ref_kind, ref_id, vector FROM embeddings WHERE 1=1"
        params: list[Any] = []

        if ref_kind is not None:
            sql += " AND ref_kind = ?"
            params.append(ref_kind)

        if ref_ids:
            placeholders = ",".join("?" * len(ref_ids))
            sql += f" AND ref_id IN ({placeholders})"
            params.extend(ref_ids)

        rows = self.store.query(sql, params)

        hits: list[SearchHit] = []
        for r in rows:
            vec = _unpack_vector(r["vector"])
            score = _cosine(query_vector, vec)
            if score >= min_score:
                hits.append(
                    SearchHit(
                        ref_kind=r["ref_kind"],
                        ref_id=r["ref_id"],
                        score=score,
                        payload={},
                    )
                )

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    def count(self, ref_kind: str | None = None) -> int:
        if ref_kind:
            row = self.store.query_one(
                "SELECT COUNT(*) AS n FROM embeddings WHERE ref_kind = ?", (ref_kind,)
            )
        else:
            row = self.store.query_one("SELECT COUNT(*) AS n FROM embeddings")
        return row["n"] if row else 0

    def delete_by_kind(self, ref_kind: str) -> int:
        cur = self.store.execute(
            "DELETE FROM embeddings WHERE ref_kind = ?", (ref_kind,)
        )
        return cur.rowcount


    def delete_by_kind_prefix(self, ref_id_prefix: str) -> int:
        """Apaga embeddings cujo ref_id comeca com o prefixo dado."""
        cur = self.store.execute(
            "DELETE FROM embeddings WHERE ref_id LIKE ?",
            (ref_id_prefix + "%",),
        )
        return cur.rowcount
