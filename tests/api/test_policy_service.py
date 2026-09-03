from api.services.policy_service import PolicyService
from core.governance import Governance
from database.connection import Database
from database.repositories.audit_repository import AuditRepository
from database.repositories.task_repository import TaskRepository


def test_sensitive_action_requires_confirmation_and_is_audited(tmp_path):
    database = Database(tmp_path / "cortex.db"); database.initialize()
    config = {"governance": {"allowed_paths": [str(tmp_path)], "audit_log": str(tmp_path / "audit.jsonl"), "require_confirmation": True}}
    service = PolicyService(Governance(config), TaskRepository(database), AuditRepository(database))
    pending = service.request("write_file", {"path": "notes.txt"})
    approved = service.request("write_file", {"path": "notes.txt"}, confirmed=True)
    assert pending["status"] == "confirmation_required"
    assert approved["status"] == "approved"
    assert len(AuditRepository(database).recent()) == 2
