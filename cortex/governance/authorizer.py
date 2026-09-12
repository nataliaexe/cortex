"""Authorizer unico. Toda tool call passa por aqui.

Regras vem de config/policy.yaml. Decisao final: allow | deny | dry_run.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cortex.config import load_policy
from cortex.memory.store import Store
from cortex.utils.logging import get_logger

log = get_logger(__name__)

Decision = str  # "allow" | "deny" | "dry_run"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expand(p: str) -> str:
    return str(Path(os.path.expanduser(p)).resolve())


@dataclass(slots=True)
class AuthResult:
    decision: Decision
    reason: str
    matched_rule: str | None = None


class Authorizer:
    def __init__(self, store: Store, policy_path: str | Path | None = None) -> None:
        self.store = store
        self.policy = load_policy(policy_path)
        self.default_action: Decision = self.policy.get("default", "deny")
        self.rules: list[dict[str, Any]] = self.policy.get("rules", []) or []

    def authorize(self, tool: str, args: dict[str, Any]) -> AuthResult:
        """Avalia se a tool pode rodar. Ordem: deny destrutivo, depois allow especifico,
        depois dry_run, depois default."""
        # 1. regras destrutivas primeiro (deny tem prioridade maxima)
        for rule in self.rules:
            if rule.get("action") != "deny":
                continue
            if self._matches(rule, tool, args):
                return AuthResult(
                    decision="deny",
                    reason=f"regra '{rule.get('name')}' bloqueou",
                    matched_rule=rule.get("name"),
                )

        # 2. allow explicito
        for rule in self.rules:
            if rule.get("action") != "allow":
                continue
            if self._matches(rule, tool, args):
                return AuthResult(
                    decision="allow",
                    reason=f"regra '{rule.get('name')}' autorizou",
                    matched_rule=rule.get("name"),
                )

        # 3. dry_run
        for rule in self.rules:
            if rule.get("action") != "dry_run":
                continue
            if self._matches(rule, tool, args):
                return AuthResult(
                    decision="dry_run",
                    reason=f"regra '{rule.get('name')}' exige dry-run",
                    matched_rule=rule.get("name"),
                )

        # 4. default
        return AuthResult(decision=self.default_action, reason="default do policy.yaml")

    def _matches(self, rule: dict[str, Any], tool: str, args: dict[str, Any]) -> bool:
        match = rule.get("match") or {}
        rule_tool = match.get("tool")
        if rule_tool is not None:
            if isinstance(rule_tool, list):
                if tool not in rule_tool:
                    return False
            elif rule_tool != tool:
                return False

        path_prefix = match.get("path_prefix")
        if path_prefix is not None:
            arg_path = args.get("path")
            if arg_path is None:
                return False
            expanded_prefix = _expand(path_prefix)
            expanded_path = _expand(str(arg_path))
            if not expanded_path.startswith(expanded_prefix):
                return False

        when = rule.get("when") or {}
        argv0_in = when.get("argv0_in")
        if argv0_in is not None:
            cmd = args.get("argv") or args.get("command")
            if isinstance(cmd, list) and cmd:
                argv0 = str(cmd[0])
            elif isinstance(cmd, str):
                argv0 = cmd.split()[0] if cmd.strip() else ""
            else:
                argv0 = ""
            if argv0 not in argv0_in:
                return False

        argv_contains_any = when.get("argv_contains_any")
        if argv_contains_any is not None:
            cmd = args.get("argv") or args.get("command")
            if isinstance(cmd, list):
                joined = " ".join(str(x) for x in cmd)
            elif isinstance(cmd, str):
                joined = cmd
            else:
                joined = ""
            if not any(pat in joined for pat in argv_contains_any):
                return False

        return True

    def log_decision(
        self,
        tool: str,
        args: dict[str, Any],
        result: AuthResult,
        session_id: str | None = None,
    ) -> str:
        """Grava a decisao na tabela audit. Retorna o id do registro."""
        audit_id = str(uuid.uuid4())
        import json
        self.store.execute(
            """
            INSERT INTO audit (id, ts, tool, args, decision, reason, result, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                _utc_now(),
                tool,
                json.dumps(args, ensure_ascii=False, default=str),
                result.decision,
                result.reason,
                None,
                session_id,
            ),
        )
        return audit_id

    def update_audit_result(self, audit_id: str, result: str) -> None:
        self.store.execute(
            "UPDATE audit SET result = ? WHERE id = ?",
            (result, audit_id),
        )
