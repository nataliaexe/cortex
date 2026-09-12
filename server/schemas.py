"""Schemas Pydantic para request/response do servidor."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------- health ----------

class HealthResponse(BaseModel):
    status: str
    version: str
    providers_available: list[str]


# ---------- chat ----------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=20000)
    session_id: str | None = None
    project_id: str | None = None
    mode: str = "default"
    auto_confirm: bool = False
    stream: bool = True


class ChatResponse(BaseModel):
    session_id: str
    text: str
    provider: str
    model: str
    was_multi_intent: bool
    tool_calls: list[dict[str, Any]] = []
    dry_runs_pending: list[dict[str, Any]] = []


# ---------- sessions ----------

class SessionCreate(BaseModel):
    title: str | None = None
    project_id: str | None = None


class SessionInfo(BaseModel):
    id: str
    created_at: str
    updated_at: str
    title: str | None = None
    metadata: dict[str, Any] = {}


class MessageInfo(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    metadata: dict[str, Any] = {}


# ---------- projects ----------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    metadata: dict[str, Any] = {}


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = {}


# ---------- sources ----------

class SourceAddNote(BaseModel):
    note: str = Field(..., min_length=1)
    title: str | None = None


class SourceAddFile(BaseModel):
    path: str = Field(..., min_length=1)
    title: str | None = None


class SourceAddUrl(BaseModel):
    url: str = Field(..., min_length=1)
    title: str | None = None


class SourceInfo(BaseModel):
    id: str
    project_id: str
    kind: str
    ref: str
    title: str | None = None
    summary: str | None = None
    indexed_at: str
    content_preview: str | None = None


class SourceSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = 5
    min_score: float = 0.3


class SourceSearchHit(BaseModel):
    source_id: str
    title: str
    kind: str
    ref: str
    chunk_index: str
    score: float


# ---------- providers ----------

class ProviderStatus(BaseModel):
    name: str
    enabled: bool
    available: bool
    reason: str = ""


# ---------- audit ----------

class AuditEntry(BaseModel):
    id: str
    ts: str
    tool: str
    args: dict[str, Any]
    decision: str
    reason: str | None = None
    result: str | None = None
    session_id: str | None = None
    project_id: str | None = None
