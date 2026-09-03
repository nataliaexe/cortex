"""Governance, approvals and audit trail for every Cortex tool action.

This module deliberately keeps policy enforcement independent from the UI.  A
CLI, voice client or web client must pass the same explicit confirmation in its
context before a state-changing action can run.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class Authorization:
    allowed: bool
    requires_confirmation: bool
    reason: str


class Governance:
    """Default-deny policy for dangerous actions, paths and commands."""

    DEFAULT_CONFIRMATION_ACTIONS = {
        "write_file", "delete_file", "create_directory", "execute_command",
        "run_code", "git_commit", "download_file", "restore_backup",
        "shutdown", "reboot", "sleep", "kill_process", "start_capture",
    }
    BLOCKED_COMMANDS = {"rm", "mkfs", "dd", "shutdown", "reboot", "poweroff", "halt"}

    # Actions that require parameter validation
    PARAMETER_VALIDATION_ACTIONS = {
        "ping_host", "trace_route", "dns_lookup", "download_file", "http_request"
    }

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        settings = config.get("governance", {})
        roots = settings.get("allowed_paths") or [config.get("system", {}).get("workspace_root", ".")]
        self.allowed_roots = tuple(Path(root).expanduser().resolve() for root in roots)
        self.require_confirmation = settings.get("require_confirmation", True)
        self.confirmation_actions = set(settings.get("confirmation_actions", self.DEFAULT_CONFIRMATION_ACTIONS))
        self.allowed_actions = set(settings.get("allowed_actions", []))
        self.audit_path = Path(settings.get("audit_log", "logs/audit.jsonl"))
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def authorize(self, action: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Authorization:
        context = context or {}
        if self.allowed_actions and action not in self.allowed_actions:
            return Authorization(False, False, "Ação não está na lista permitida pela política.")

        # Validate parameters for sensitive actions FIRST (before confirmation check)
        if action in self.PARAMETER_VALIDATION_ACTIONS:
            validation_error = self._validate_action_parameters(action, params)
            if validation_error:
                return Authorization(False, False, f"Parâmetros inválidos: {validation_error}")

        if action in self.confirmation_actions and self.require_confirmation:
            confirmed = set(context.get("confirmed_actions", []))
            if action not in confirmed and "*" not in confirmed:
                return Authorization(False, True, "Ação altera o sistema, dados ou rede e requer confirmação humana.")

        return Authorization(True, False, "Permitida pela política local.")

    def ensure_path(self, value: str | Path, *, must_exist: bool = False) -> Path:
        path = Path(value).expanduser().resolve(strict=must_exist)
        if not any(path == root or root in path.parents for root in self.allowed_roots):
            raise PermissionError(f"Caminho fora das áreas autorizadas: {path}")
        return path

    def validate_command(self, command: Iterable[str]) -> list[str]:
        argv = list(command)
        if not argv or not all(isinstance(part, str) and part for part in argv):
            raise ValueError("O comando deve ser uma lista não vazia de argumentos.")
        program = Path(argv[0]).name.lower()
        if program in self.BLOCKED_COMMANDS:
            raise PermissionError(f"Comando bloqueado pela política: {program}")
        return argv

    def audit(self, action: str, authorization: Authorization, *, params: Optional[Dict[str, Any]] = None, outcome: str = "requested") -> None:
        safe_params = {key: "[redacted]" if any(word in key.lower() for word in ("password", "token", "secret", "key")) else str(value)[:500]
                       for key, value in (params or {}).items()}
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(), "action": action,
            "outcome": outcome, "authorization": asdict(authorization), "params": safe_params,
        }
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def status(self) -> Dict[str, Any]:
        return {
            "allowed_paths": [str(path) for path in self.allowed_roots],
            "require_confirmation": self.require_confirmation,
            "confirmation_actions": sorted(self.confirmation_actions),
            "audit_log": str(self.audit_path),
        }

    def _validate_action_parameters(self, action: str, params: Dict[str, Any]) -> Optional[str]:
        """Valida parâmetros para ações específicas"""
        if action in ("ping_host", "trace_route"):
            return self._validate_network_target(params.get("host"))
        elif action == "dns_lookup":
            return self._validate_domain(params.get("domain"))
        elif action in ("download_file", "http_request"):
            return self._validate_url(params.get("url"))
        return None

    def _validate_network_target(self, host: Any) -> Optional[str]:
        """Valida que host foi especificado explicitamente (sem default público)"""
        if not host:
            return "host deve ser especificado explicitamente"
        return None

    def _validate_domain(self, domain: Any) -> Optional[str]:
        """Valida que domain foi especificado explicitamente (sem default público)"""
        if not domain:
            return "domain deve ser especificado explicitamente"
        return None

    def _validate_url(self, url: Any) -> Optional[str]:
        """Valida URL básica"""
        if not url:
            return "url deve ser especificada"
        return None
