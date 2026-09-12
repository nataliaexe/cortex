"""Rotas de providers."""

from __future__ import annotations

from fastapi import APIRouter

from server.deps import get_state
from server.schemas import ProviderStatus

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderStatus])
async def list_providers() -> list[ProviderStatus]:
    state = get_state()
    return [
        ProviderStatus(
            name=s.name,
            enabled=s.enabled,
            available=s.available,
            reason=s.reason,
        )
        for s in state.registry.status()
    ]
