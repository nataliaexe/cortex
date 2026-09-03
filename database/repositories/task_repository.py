from __future__ import annotations

from database.connection import Database
from .base import from_json, new_id, now, to_json


class TaskRepository:
    def __init__(self, database: Database): self.database = database

    def create(self, requested_action: str, parameters: dict | None = None, status: str = "requested") -> dict:
        task = {"id": new_id(), "requested_action": requested_action, "parameters": parameters or {}, "status": status, "created_at": now()}
        with self.database.connection() as conn:
            conn.execute("INSERT INTO tasks (id, requested_action, parameters_json, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (task["id"], requested_action, to_json(task["parameters"]), status, task["created_at"], task["created_at"]))
        return task

    def update(self, task_id: str, status: str, validation: dict | None = None, result: dict | None = None) -> None:
        with self.database.connection() as conn:
            conn.execute("UPDATE tasks SET status=?, validation_json=COALESCE(?, validation_json), result_json=COALESCE(?, result_json), updated_at=? WHERE id=?", (status, to_json(validation) if validation is not None else None, to_json(result) if result is not None else None, now(), task_id))

    def get(self, task_id: str) -> dict | None:
        with self.database.connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row: return None
        task = dict(row); task["parameters"] = from_json(task.pop("parameters_json"), {}); task["validation"] = from_json(task.pop("validation_json")); task["result"] = from_json(task.pop("result_json")); return task
