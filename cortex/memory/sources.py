"""Indexacao de fontes de projeto.

Uma fonte pode ser:
  - file: caminho local de arquivo de texto
  - url: URL http/https (baixa e extrai texto)
  - note: texto puro digitado pelo usuario
  - repo: caminho de repositorio git (indexa arquivos de codigo)

Cada fonte gera N embeddings (N = numero de chunks).
O conteudo completo e os metadados ficam em project_sources.
"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from cortex.memory.embeddings import EmbeddingStore
from cortex.memory.store import Store
from cortex.models.local import LocalClient
from cortex.utils.logging import get_logger

log = get_logger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_FILE_BYTES = 500_000
MAX_URL_BYTES = 500_000


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto em chunks com overlap. Quebra por paragrafo quando possivel."""
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # tenta quebrar num \n\n proximo
        window = text[start:end]
        cut = window.rfind("\n\n")
        if cut > size // 2:
            end = start + cut + 2
        else:
            # tenta quebra de linha simples
            cut = window.rfind("\n")
            if cut > size // 2:
                end = start + cut + 1

        chunks.append(text[start:end])
        # proximo comeca com overlap
        start = max(start + 1, end - overlap)

    return chunks


def _extract_text_from_html(html: str) -> str:
    """Extrai texto legivel de HTML. Bem rudimentar mas funcional."""
    # remove script/style
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # decodifica entidades basicas
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
    )
    # normaliza espacos
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


@dataclass(slots=True)
class AddSourceResult:
    source_id: str
    kind: str
    ref: str
    title: str
    chunks: int
    indexed: bool
    error: str | None = None


class SourcesRepo:
    """CRUD e indexacao de fontes de projeto."""

    def __init__(
        self,
        store: Store,
        embeddings: EmbeddingStore,
        local_client: LocalClient,
    ) -> None:
        self.store = store
        self.embeddings = embeddings
        self.local = local_client

    # ---------- CRUD ----------

    def list(self, project_id: str) -> list[dict[str, Any]]:
        rows = self.store.query(
            "SELECT * FROM project_sources WHERE project_id = ? ORDER BY indexed_at DESC",
            (project_id,),
        )
        return [self._row_to_source(r) for r in rows]

    def get(self, source_id: str) -> dict[str, Any] | None:
        row = self.store.query_one(
            "SELECT * FROM project_sources WHERE id = ?", (source_id,)
        )
        return self._row_to_source(row) if row else None

    def delete(self, source_id: str) -> bool:
        # apaga embeddings primeiro
        n = self.embeddings.delete_by_kind_prefix(f"source:{source_id}:")
        cur = self.store.execute(
            "DELETE FROM project_sources WHERE id = ?", (source_id,)
        )
        return cur.rowcount > 0

    # ---------- indexacao ----------

    async def add_file(
        self,
        project_id: str,
        path: str,
        title: str | None = None,
    ) -> AddSourceResult:
        p = Path(os.path.expanduser(path)).resolve()
        if not p.exists():
            return AddSourceResult("", "file", str(p), title or p.name, 0, False, "arquivo nao existe")
        if not p.is_file():
            return AddSourceResult("", "file", str(p), title or p.name, 0, False, "nao e arquivo")

        size = p.stat().st_size
        if size > MAX_FILE_BYTES:
            return AddSourceResult(
                "", "file", str(p), title or p.name, 0, False,
                f"arquivo muito grande ({size} bytes > {MAX_FILE_BYTES})",
            )

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return AddSourceResult("", "file", str(p), title or p.name, 0, False, f"erro de IO: {e}")

        return await self._index_content(
            project_id=project_id,
            kind="file",
            ref=str(p),
            title=title or p.name,
            content=content,
        )

    async def add_url(
        self,
        project_id: str,
        url: str,
        title: str | None = None,
    ) -> AddSourceResult:
        if not url.startswith(("http://", "https://")):
            return AddSourceResult("", "url", url, title or url, 0, False, "URL invalida")

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "Cortex/0.1"},
            ) as client:
                r = await client.get(url)
                r.raise_for_status()
                if len(r.content) > MAX_URL_BYTES:
                    return AddSourceResult(
                        "", "url", url, title or url, 0, False,
                        f"conteudo muito grande ({len(r.content)} bytes)",
                    )
                raw = r.text
        except httpx.HTTPError as e:
            return AddSourceResult("", "url", url, title or url, 0, False, f"erro HTTP: {e}")

        # extrai texto
        ctype = ""
        try:
            ctype = r.headers.get("content-type", "")
        except Exception:
            pass
        if "html" in ctype.lower() or raw.lstrip().startswith("<"):
            content = _extract_text_from_html(raw)
        else:
            content = raw

        if not content.strip():
            return AddSourceResult("", "url", url, title or url, 0, False, "sem texto extraivel")

        return await self._index_content(
            project_id=project_id,
            kind="url",
            ref=url,
            title=title or url,
            content=content,
        )

    async def add_note(
        self,
        project_id: str,
        note: str,
        title: str | None = None,
    ) -> AddSourceResult:
        note = note.strip()
        if not note:
            return AddSourceResult("", "note", "", title or "nota", 0, False, "nota vazia")
        return await self._index_content(
            project_id=project_id,
            kind="note",
            ref=note[:100],
            title=title or note[:60],
            content=note,
        )

    # ---------- interno ----------

    async def _index_content(
        self,
        project_id: str,
        kind: str,
        ref: str,
        title: str,
        content: str,
    ) -> AddSourceResult:
        source_id = str(uuid.uuid4())
        chunks = _chunk_text(content)
        now = _utc_now()

        # guarda a fonte
        self.store.execute(
            """
            INSERT INTO project_sources (id, project_id, kind, ref, title, summary, content, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                project_id,
                kind,
                ref,
                title,
                content[:300],
                content,
                now,
            ),
        )

        # gera embeddings
        try:
            indexed = 0
            for i, chunk in enumerate(chunks):
                vec = await self.local.embed(chunk)
                ref_id = f"source:{source_id}:{i}"
                self.embeddings.put(
                    ref_kind="project_source",
                    ref_id=ref_id,
                    vector=vec,
                    model=self.local.cfg.embed_model,
                )
                indexed += 1

            log.info("source_indexed", source_id=source_id, kind=kind, chunks=indexed)
            return AddSourceResult(
                source_id=source_id,
                kind=kind,
                ref=ref,
                title=title,
                chunks=indexed,
                indexed=True,
            )
        except Exception as e:
            log.error("source_index_failed", source_id=source_id, error=str(e))
            # rollback parcial: apaga embeddings que conseguiu criar
            self.embeddings.delete_by_kind_prefix(f"source:{source_id}:")
            return AddSourceResult(
                source_id=source_id,
                kind=kind,
                ref=ref,
                title=title,
                chunks=0,
                indexed=False,
                error=f"erro ao indexar: {type(e).__name__}: {e}",
            )

    async def search(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Busca semantica nas fontes do projeto."""
        vec = await self.local.embed(query)

        # lista os source_ids do projeto
        rows = self.store.query(
            "SELECT id FROM project_sources WHERE project_id = ?", (project_id,)
        )
        source_ids = [r["id"] for r in rows]
        if not source_ids:
            return []

        # filtra embeddings por prefixo (ref_id comeca com "source:<id>:")
        # nao temos LIKE nativo para prefixos multiplos; fazemos em Python
        all_hits = self.embeddings.search(
            query_vector=vec,
            ref_kind="project_source",
            top_k=200,   # pega mais para depois filtrar
        )
        filtered: list[dict[str, Any]] = []
        for hit in all_hits:
            if hit.score < min_score:
                continue
            # hit.ref_id = "source:<source_id>:<idx>"
            parts = hit.ref_id.split(":")
            if len(parts) < 3:
                continue
            sid = parts[1]
            if sid not in source_ids:
                continue
            chunk_idx = parts[2] if len(parts) > 2 else "?"

            source_row = self.store.query_one(
                "SELECT * FROM project_sources WHERE id = ?", (sid,)
            )
            if source_row is None:
                continue
            filtered.append({
                "source_id": sid,
                "title": source_row["title"],
                "kind": source_row["kind"],
                "ref": source_row["ref"],
                "chunk_index": chunk_idx,
                "score": round(hit.score, 4),
            })
            if len(filtered) >= top_k:
                break

        return filtered

    @staticmethod
    def _row_to_source(r) -> dict[str, Any]:
        return {
            "id": r["id"],
            "project_id": r["project_id"],
            "kind": r["kind"],
            "ref": r["ref"],
            "title": r["title"],
            "summary": r["summary"],
            "indexed_at": r["indexed_at"],
            "content_preview": (r["content"] or "")[:200],
        }
