"""Contrato de toda tool do Cortex.

Toda tool: declara nome, descricao, schema de args, se e destrutiva,
e implementa run(). Se destrutiva, implementa preview() tambem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from cortex.governance.dry_run import DryRunPreview


@dataclass(slots=True)
class ToolResult:
    ok: bool
    output: str = ""
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "output": self.output,
            "error": self.error,
            "meta": self.meta,
        }


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    schema: dict[str, Any]
    destructive: bool
    requires_sandbox: bool

    def run(self, args: dict[str, Any], ctx: "ToolContext") -> ToolResult: ...
    def preview(self, args: dict[str, Any]) -> DryRunPreview: ...


@dataclass(slots=True)
class ToolContext:
    """Contexto passado a toda tool em run()."""

    session_id: str
    memory: Any
    config: Any
    sandbox_dir: str | None = None
    dry_run: bool = False


class BaseTool:
    """Base opcional que ja preenche defaults. Ferramentas podem herdar dela."""

    name: str = "base"
    description: str = ""
    schema: dict[str, Any] = {}
    destructive: bool = False
    requires_sandbox: bool = False

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        raise NotImplementedError

    def preview(self, args: dict[str, Any]) -> DryRunPreview:
        return DryRunPreview(
            tool=self.name,
            args=args,
            description=f"executar {self.name}",
            impact="reversible",
        )
