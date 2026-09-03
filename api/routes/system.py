from fastapi import APIRouter

from core.governance import Governance
from database.repositories.audit_repository import AuditRepository
from fastapi.responses import PlainTextResponse
from observability.metrics import metrics


def router(config: dict, audit: AuditRepository, get_engine) -> APIRouter:
    api = APIRouter(prefix="/api", tags=["system"])

    @api.get("/health")
    async def health():
        from core.local_llm import LocalLLM
        models = await LocalLLM(config).model_status()
        return {"status": "healthy", "database": "ready", "ollama": models["ollama_available"]}

    @api.get("/status")
    async def status():
        engine = get_engine()
        return {"status": "running" if engine else "standalone", "llm_enabled": bool(engine and engine.local_llm.enabled), "database": "sqlite"}

    @api.get("/governance/status")
    def governance_status(): return Governance(config).status()

    @api.get("/audit-events")
    def audit_events(limit: int = 100): return {"events": audit.recent(min(max(limit, 1), 500))}

    @api.get("/metrics", response_class=PlainTextResponse)
    def metric_output(): return metrics.prometheus()

    @api.get("/models/status")
    async def models_status():
        from core.local_llm import LocalLLM
        return await LocalLLM(config).model_status()

    return api
