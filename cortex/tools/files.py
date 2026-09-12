"""Tools de arquivo. Leitura, escrita, listagem, remocao."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cortex.governance.dry_run import DryRunPreview
from cortex.tools.base import BaseTool, ToolContext, ToolResult


def _resolve_within(path: str, allowed_roots: list[str]) -> Path:
    """Resolve path e garante que esta dentro de um dos roots permitidos."""
    expanded = Path(os.path.expanduser(path)).resolve()
    for root in allowed_roots:
        root_expanded = Path(os.path.expanduser(root)).resolve()
        try:
            expanded.relative_to(root_expanded)
            return expanded
        except ValueError:
            continue
    raise PermissionError(
        f"path fora das raizes permitidas: {expanded}. roots={allowed_roots}"
    )


class ListFilesTool(BaseTool):
    name = "files.list"
    description = "Lista arquivos e diretorios dentro de um caminho permitido."
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "diretorio a listar"},
            "recursive": {"type": "boolean", "default": False},
            "max_entries": {"type": "integer", "default": 200},
        },
        "required": ["path"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        allowed_roots = ctx.config.tools.files.allowed_roots
        try:
            target = _resolve_within(args["path"], allowed_roots)
        except PermissionError as e:
            return ToolResult(ok=False, error=str(e))

        if not target.exists():
            return ToolResult(ok=False, error=f"path inexistente: {target}")
        if not target.is_dir():
            return ToolResult(ok=False, error=f"nao e diretorio: {target}")

        recursive = bool(args.get("recursive", False))
        max_entries = int(args.get("max_entries", 200))

        entries: list[str] = []
        try:
            if recursive:
                for p in target.rglob("*"):
                    entries.append(str(p.relative_to(target)))
                    if len(entries) >= max_entries:
                        break
            else:
                for p in sorted(target.iterdir()):
                    suffix = "/" if p.is_dir() else ""
                    entries.append(p.name + suffix)
                    if len(entries) >= max_entries:
                        break
        except OSError as e:
            return ToolResult(ok=False, error=f"erro de IO: {e}")

        return ToolResult(
            ok=True,
            output="\n".join(entries),
            meta={"count": len(entries), "path": str(target)},
        )


class ReadFileTool(BaseTool):
    name = "files.read"
    description = "Le o conteudo de um arquivo de texto dentro de uma raiz permitida."
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer"},
        },
        "required": ["path"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        allowed_roots = ctx.config.tools.files.allowed_roots
        try:
            target = _resolve_within(args["path"], allowed_roots)
        except PermissionError as e:
            return ToolResult(ok=False, error=str(e))

        if not target.exists():
            return ToolResult(ok=False, error=f"arquivo inexistente: {target}")
        if not target.is_file():
            return ToolResult(ok=False, error=f"nao e arquivo: {target}")

        max_bytes = int(
            args.get("max_bytes", ctx.config.tools.files.max_read_bytes)
        )
        try:
            size = target.stat().st_size
            with target.open("r", encoding="utf-8", errors="replace") as fh:
                content = fh.read(max_bytes)
        except OSError as e:
            return ToolResult(ok=False, error=f"erro de IO: {e}")

        truncated = size > max_bytes
        return ToolResult(
            ok=True,
            output=content,
            meta={
                "path": str(target),
                "size": size,
                "truncated": truncated,
                "max_bytes": max_bytes,
            },
        )


class WriteFileTool(BaseTool):
    name = "files.write"
    description = "Escreve conteudo em um arquivo. Requer dry-run por padrao."
    destructive = True
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "append": {"type": "boolean", "default": False},
        },
        "required": ["path", "content"],
    }

    def preview(self, args: dict[str, Any]) -> DryRunPreview:
        path = args.get("path", "?")
        content = args.get("content", "")
        append = args.get("append", False)
        mode = "append" if append else "sobrescrever"
        preview_text = content[:500]
        if len(content) > 500:
            preview_text += "\n...(truncado)"
        return DryRunPreview(
            tool=self.name,
            args=args,
            description=f"{mode} {path} com {len(content)} bytes",
            impact="reversible",
            diff=preview_text,
        )

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        allowed_roots = ctx.config.tools.files.allowed_roots
        try:
            target = _resolve_within(args["path"], allowed_roots)
        except PermissionError as e:
            return ToolResult(ok=False, error=str(e))

        content = args.get("content", "")
        append = bool(args.get("append", False))
        existed = target.exists()
        old_size = target.stat().st_size if existed else 0

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with target.open(mode, encoding="utf-8") as fh:
                fh.write(content)
        except OSError as e:
            return ToolResult(ok=False, error=f"erro de IO: {e}")

        new_size = target.stat().st_size
        return ToolResult(
            ok=True,
            output=f"escrito {len(content)} bytes em {target}",
            meta={
                "path": str(target),
                "bytes_written": len(content),
                "existed": existed,
                "old_size": old_size,
                "new_size": new_size,
                "append": append,
            },
        )


class DeleteFileTool(BaseTool):
    name = "files.delete"
    description = "Remove um arquivo. Requer dry-run por padrao."
    destructive = True
    schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    def preview(self, args: dict[str, Any]) -> DryRunPreview:
        path = args.get("path", "?")
        return DryRunPreview(
            tool=self.name,
            args=args,
            description=f"remover {path}",
            impact="irreversible",
        )

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        allowed_roots = ctx.config.tools.files.allowed_roots
        try:
            target = _resolve_within(args["path"], allowed_roots)
        except PermissionError as e:
            return ToolResult(ok=False, error=str(e))

        if not target.exists():
            return ToolResult(ok=False, error=f"arquivo inexistente: {target}")
        if target.is_dir():
            return ToolResult(
                ok=False,
                error="files.delete nao remove diretorios; use shell.run com cuidado",
            )
        try:
            size = target.stat().st_size
            target.unlink()
        except OSError as e:
            return ToolResult(ok=False, error=f"erro de IO: {e}")

        return ToolResult(
            ok=True,
            output=f"removido {target}",
            meta={"path": str(target), "size_removed": size},
        )
