from fastapi import APIRouter, HTTPException

from api.schemas.task import TaskCreate
from api.services.policy_service import PolicyService
from database.repositories.task_repository import TaskRepository


def router(policy: PolicyService, tasks: TaskRepository) -> APIRouter:
    api = APIRouter(prefix="/api/tasks", tags=["tasks"])

    @api.post("")
    def create(payload: TaskCreate):
        return policy.request(payload.requested_action, payload.parameters, payload.confirmed)

    @api.get("/{task_id}")
    def get(task_id: str):
        task = tasks.get(task_id)
        if not task: raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        return task

    return api
