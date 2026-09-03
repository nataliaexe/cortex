"""Boundary between intent/planning and any executable action."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.governance import Governance
from database.repositories.audit_repository import AuditRepository
from database.repositories.task_repository import TaskRepository
from observability.metrics import metrics


class PolicyService:
    def __init__(self, governance: Governance, tasks: TaskRepository, audit: AuditRepository):
        self.governance, self.tasks, self.audit = governance, tasks, audit

    def request(self, action: str, parameters: dict[str, Any], confirmed: bool = False) -> dict:
        task = self.tasks.create(action, parameters)
        context = {"confirmed_actions": [action]} if confirmed else {}
        authorization = self.governance.authorize(action, parameters, context)
        outcome = "approved" if authorization.allowed else ("confirmation_required" if authorization.requires_confirmation else "denied")
        self.tasks.update(task["id"], outcome, asdict(authorization))
        self.governance.audit(action, authorization, params=parameters, outcome=outcome)
        self.audit.record(action, outcome, asdict(authorization), parameters)
        metrics.increment(f"policy_{outcome}")
        task.update({"status": outcome, "validation": asdict(authorization)})
        return task
