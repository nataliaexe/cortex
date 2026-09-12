"""Mecanismo de dry-run.

Quando o authorizer decide 'dry_run', o executor chama preview() da tool,
mostra ao usuario, e so executa apos confirmacao explicita.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class DryRunPreview:
    tool: str
    args: dict[str, Any]
    description: str
    impact: str  # "read_only" | "reversible" | "irreversible"
    diff: str | None = None


class DryRunnable(Protocol):
    def preview(self, args: dict[str, Any]) -> DryRunPreview: ...


class ConfirmationRequired(Exception):
    """Levantada quando um dry-run precisa de confirmacao e nao houve."""

    def __init__(self, preview: DryRunPreview) -> None:
        self.preview = preview
        super().__init__(f"confirmacao requerida para {preview.tool}")


def format_preview(preview: DryRunPreview) -> str:
    lines = [
        f"[dry-run] tool: {preview.tool}",
        f"[dry-run] impacto: {preview.impact}",
        f"[dry-run] descricao: {preview.description}",
    ]
    if preview.diff:
        lines.append("[dry-run] diff:")
        lines.append(preview.diff)
    return "\n".join(lines)
