"""Tool de shell. Execucao com argv explicito, sem shell meta, com timeout."""

from __future__ import annotations

import shlex
import subprocess
from typing import Any

from cortex.governance.dry_run import DryRunPreview
from cortex.tools.base import BaseTool, ToolContext, ToolResult

FORBIDDEN_META = [";", "&&", "||", "|", "`", "$(", ">", "<", "&"]


def _to_argv(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        return shlex.split(raw)
    raise ValueError("argv deve ser list[str] ou string")


def _has_shell_meta(argv: list[str]) -> str | None:
    for token in argv:
        for meta in FORBIDDEN_META:
            if meta in token:
                return meta
    return None


class ShellRunTool(BaseTool):
    name = "shell.run"
    description = (
        "Executa um comando com argv explicito (sem shell). "
        "Nao aceita pipes, redirecionamento ou meta-caracteres. "
        "Requer dry-run quando o comando nao esta na allowlist."
    )
    destructive = True
    schema = {
        "type": "object",
        "properties": {
            "argv": {
                "type": "array",
                "items": {"type": "string"},
                "description": "comando e argumentos, primeiro item e o executavel",
            },
            "cwd": {"type": "string", "description": "diretorio de trabalho"},
            "timeout_seconds": {"type": "integer"},
        },
        "required": ["argv"],
    }

    def preview(self, args: dict[str, Any]) -> DryRunPreview:
        argv = args.get("argv", [])
        rendered = " ".join(shlex.quote(str(a)) for a in argv) if isinstance(argv, list) else str(argv)
        return DryRunPreview(
            tool=self.name,
            args=args,
            description=f"executar: {rendered}",
            impact="reversible",
        )

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        try:
            argv = _to_argv(args.get("argv"))
        except ValueError as e:
            return ToolResult(ok=False, error=str(e))

        if not argv:
            return ToolResult(ok=False, error="argv vazio")

        if ctx.config.tools.shell.forbid_shell_meta:
            meta = _has_shell_meta(argv)
            if meta is not None:
                return ToolResult(
                    ok=False,
                    error=f"meta-caractere de shell proibido: {meta!r}",
                )

        argv0 = argv[0]
        allowlist = ctx.config.tools.shell.allowlist_argv0
        if argv0 not in allowlist:
            return ToolResult(
                ok=False,
                error=(
                    f"comando {argv0!r} nao esta na allowlist. "
                    f"allowlist atual: {allowlist}"
                ),
            )

        cwd = args.get("cwd")
        timeout = int(
            args.get("timeout_seconds", ctx.config.tools.shell.timeout_seconds)
        )

        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                ok=False,
                error=f"timeout de {timeout}s excedido",
                meta={"argv": argv, "timeout_seconds": timeout},
            )
        except FileNotFoundError:
            return ToolResult(ok=False, error=f"executavel nao encontrado: {argv0}")
        except OSError as e:
            return ToolResult(ok=False, error=f"erro de execucao: {e}")

        ok = proc.returncode == 0
        return ToolResult(
            ok=ok,
            output=proc.stdout,
            error=proc.stderr if proc.stderr else None,
            meta={
                "argv": argv,
                "returncode": proc.returncode,
                "cwd": cwd,
                "timeout_seconds": timeout,
            },
        )
