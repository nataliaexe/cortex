"""Rota de health check."""

from __future__ import annotations

from fastapi import APIRouter

from server.deps import get_state
from server.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    state = get_state()
    available = state.registry.available_providers()
    return HealthResponse(
        status="ok",
        version=state.cfg.app.version,
        providers_available=available,
    )
