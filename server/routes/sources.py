"""Rotas de fontes de projeto."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.deps import get_state
from server.schemas import (
    SourceAddFile,
    SourceAddNote,
    SourceAddUrl,
    SourceInfo,
    SourceSearchHit,
    SourceSearchRequest,
)

router = APIRouter(prefix="/projects/{project_ref}/sources", tags=["sources"])


def _resolve_project(project_ref: str):
    state = get_state()
    p = state.memory.projects.resolve(project_ref)
    if p is None:
        raise HTTPException(status_code=404, detail=f"projeto '{project_ref}' nao encontrado")
    return p


@router.get("", response_model=list[SourceInfo])
async def list_sources(project_ref: str) -> list[SourceInfo]:
    p = _resolve_project(project_ref)
    state = get_state()
    return [SourceInfo(**s) for s in state.memory.sources.list(p["id"])]


@router.post("/note", response_model=SourceInfo, status_code=201)
async def add_note(project_ref: str, payload: SourceAddNote) -> SourceInfo:
    p = _resolve_project(project_ref)
    state = get_state()
    r = await state.memory.sources.add_note(p["id"], payload.note, title=payload.title)
    if not r.indexed:
        raise HTTPException(status_code=500, detail=f"falha na indexacao: {r.error}")
    s = state.memory.sources.get(r.source_id)
    if s is None:
        raise HTTPException(status_code=500, detail="fonte criada mas nao encontrada")
    return SourceInfo(**s)


@router.post("/file", response_model=SourceInfo, status_code=201)
async def add_file(project_ref: str, payload: SourceAddFile) -> SourceInfo:
    p = _resolve_project(project_ref)
    state = get_state()
    r = await state.memory.sources.add_file(p["id"], payload.path, title=payload.title)
    if not r.indexed:
        raise HTTPException(status_code=400, detail=f"falha na indexacao: {r.error}")
    s = state.memory.sources.get(r.source_id)
    if s is None:
        raise HTTPException(status_code=500, detail="fonte criada mas nao encontrada")
    return SourceInfo(**s)


@router.post("/url", response_model=SourceInfo, status_code=201)
async def add_url(project_ref: str, payload: SourceAddUrl) -> SourceInfo:
    p = _resolve_project(project_ref)
    state = get_state()
    r = await state.memory.sources.add_url(p["id"], payload.url, title=payload.title)
    if not r.indexed:
        raise HTTPException(status_code=400, detail=f"falha na indexacao: {r.error}")
    s = state.memory.sources.get(r.source_id)
    if s is None:
        raise HTTPException(status_code=500, detail="fonte criada mas nao encontrada")
    return SourceInfo(**s)


@router.delete("/{source_id}", status_code=204)
async def delete_source(project_ref: str, source_id: str) -> None:
    _resolve_project(project_ref)
    state = get_state()
    s = state.memory.sources.get(source_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"fonte '{source_id}' nao encontrada")
    state.memory.sources.delete(source_id)


@router.post("/search", response_model=list[SourceSearchHit])
async def search_sources(project_ref: str, payload: SourceSearchRequest) -> list[SourceSearchHit]:
    p = _resolve_project(project_ref)
    state = get_state()
    hits = await state.memory.sources.search(
        p["id"], payload.query, top_k=payload.top_k, min_score=payload.min_score
    )
    return [SourceSearchHit(**h) for h in hits]
