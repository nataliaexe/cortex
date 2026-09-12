"""Rotas de projetos."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.deps import get_state
from server.schemas import ProjectCreate, ProjectInfo, SessionInfo

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectInfo])
async def list_projects() -> list[ProjectInfo]:
    state = get_state()
    return [ProjectInfo(**p) for p in state.memory.projects.list()]


@router.post("", response_model=ProjectInfo, status_code=201)
async def create_project(payload: ProjectCreate) -> ProjectInfo:
    state = get_state()
    try:
        pid = state.memory.projects.create(
            name=payload.name,
            description=payload.description,
            metadata=payload.metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))

    p = state.memory.projects.get(pid)
    if p is None:
        raise HTTPException(status_code=500, detail="projeto criado mas nao encontrado")
    return ProjectInfo(**p)


@router.get("/{project_ref}", response_model=ProjectInfo)
async def get_project(project_ref: str) -> ProjectInfo:
    state = get_state()
    p = state.memory.projects.resolve(project_ref)
    if p is None:
        raise HTTPException(status_code=404, detail=f"projeto '{project_ref}' nao encontrado")
    return ProjectInfo(**p)


@router.delete("/{project_ref}", status_code=204)
async def delete_project(project_ref: str) -> None:
    state = get_state()
    p = state.memory.projects.resolve(project_ref)
    if p is None:
        raise HTTPException(status_code=404, detail=f"projeto '{project_ref}' nao encontrado")
    state.memory.projects.delete(p["id"])


@router.get("/{project_ref}/sessions", response_model=list[SessionInfo])
async def list_project_sessions(project_ref: str) -> list[SessionInfo]:
    state = get_state()
    p = state.memory.projects.resolve(project_ref)
    if p is None:
        raise HTTPException(status_code=404, detail=f"projeto '{project_ref}' nao encontrado")
    return [SessionInfo(**s) for s in state.memory.projects.sessions_for_project(p["id"])]
