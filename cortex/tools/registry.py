"""Registro central de tools.

Toda tool se registra aqui. O nucleo consulta o registry, nunca importa
modulos de tools diretamente. Isso mantem a superficie pequena e permite
ligar/desligar tools por config no futuro.
"""

from __future__ import annotations

from typing import Any, Iterator

from cortex.tools.base import Tool
from cortex.utils.logging import get_logger

log = get_logger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool duplicada: {tool.name}")
        self._tools[tool.name] = tool
        log.debug("tool_registered", tool=tool.name)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def require(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"tool nao registrada: {name}")
        return tool

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def all(self) -> list[Tool]:
        return [self._tools[n] for n in self.names()]

    def catalogue(self) -> list[dict[str, Any]]:
        """Descricao completa para expor em prompts do LLM e na API."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "schema": t.schema,
                "destructive": t.destructive,
                "requires_sandbox": t.requires_sandbox,
            }
            for t in self.all()
        ]

    def __iter__(self) -> Iterator[Tool]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self._tools)


_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    return _global_registry


def register_defaults() -> ToolRegistry:
    """Registra as tools built-in. Idempotente."""
    reg = get_registry()

    from cortex.tools.files import (
        ListFilesTool,
        ReadFileTool,
        WriteFileTool,
        DeleteFileTool,
    )
    from cortex.tools.shell import ShellRunTool

    builtin = [
        ListFilesTool(),
        ReadFileTool(),
        WriteFileTool(),
        DeleteFileTool(),
        ShellRunTool(),
    ]
    for t in builtin:
        if t.name not in reg._tools:
            reg.register(t)
    return reg
