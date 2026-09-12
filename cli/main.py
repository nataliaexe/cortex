"""Entry point do binario `cortex`."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cortex.config import load_config
from cortex.memory.facade import Memory
from cortex.models.registry import ModelRegistry
from cortex.nucleus.loop import CortexLoop
from cortex.nucleus.router import Router
from cortex.tools.registry import register_defaults
from cortex.utils.logging import configure_logging, get_logger

app = typer.Typer(
    name="cortex",
    help="Assistente pessoal hibrido, governado e offline-first.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


def _bootstrap():
    cfg = load_config()
    configure_logging(cfg.app.log_file, cfg.app.log_level)
    log = get_logger("cli")
    log.info("cortex_bootstrap", version=cfg.app.version)

    memory = Memory(cfg.database.path)
    registry = ModelRegistry(cfg)
    router = Router(cfg, registry)
    register_defaults()
    loop = CortexLoop(cfg, memory, registry, router)
    return cfg, memory, registry, router, loop


@app.command()
def repl() -> None:
    """Abre o REPL interativo do Cortex."""
    from cli.repl import run_repl

    cfg, memory, registry, router, loop = _bootstrap()
    try:
        asyncio.run(run_repl(loop))
    finally:
        memory.close()


@app.command()
def ask(
    text: str = typer.Argument(..., help="Pergunta unica, sem entrar no REPL"),
    auto_confirm: bool = typer.Option(False, "--auto-confirm", help="Executa tools destrutivas sem pedir confirmacao"),
) -> None:
    """Faz uma pergunta unica e imprime a resposta."""
    cfg, memory, registry, router, loop = _bootstrap()
    try:
        async def _run():
            sid = memory.sessions.create(title="cli-ask")
            result = await loop.run_turn(sid, text, auto_confirm=auto_confirm)
            console.print(result.final_text)
            if result.tool_calls:
                console.print("\n[dim]tools executadas:[/dim]")
                for tc in result.tool_calls:
                    flag = "OK" if tc["ok"] else "FAIL"
                    console.print(f"  [{flag}] {tc['tool']}")
            if result.dry_runs_pending:
                console.print("\n[yellow]dry-runs pendentes (nao executados):[/yellow]")
                for p in result.dry_runs_pending:
                    console.print(f"  {p.description}")

        asyncio.run(_run())
    finally:
        memory.close()


@app.command("providers")
def providers_cmd(
    test: bool = typer.Option(False, "--test", help="Testa cada provider com uma chamada curta"),
) -> None:
    """Lista providers e status."""
    cfg, memory, registry, router, loop = _bootstrap()
    try:
        table = Table(title="Providers")
        table.add_column("nome")
        table.add_column("enabled")
        table.add_column("disponivel")
        table.add_column("motivo")

        for s in registry.status():
            table.add_row(
                s.name,
                "sim" if s.enabled else "nao",
                "sim" if s.available else "nao",
                s.reason or "",
            )
        console.print(table)

        if test:
            console.print("\n[bold]testando providers...[/bold]")

            async def _test():
                from cortex.models.local import ChatMessage

                msgs = [ChatMessage(role="user", content="Diga apenas: ok")]
                for s in registry.status():
                    if not s.available:
                        console.print(f"  {s.name}: pulando ({s.reason})")
                        continue
                    try:
                        text = await registry.chat_with(s.name, msgs, temperature=0.1)
                        console.print(f"  {s.name}: OK -> {text.strip()[:40]}")
                    except Exception as e:
                        console.print(f"  {s.name}: FALHOU -> {type(e).__name__}: {str(e)[:80]}")

            asyncio.run(_test())
    finally:
        memory.close()


@app.command("tools")
def tools_cmd() -> None:
    """Lista tools registradas."""
    cfg, memory, registry, router, loop = _bootstrap()
    try:
        table = Table(title="Tools")
        table.add_column("nome")
        table.add_column("destrutiva")
        table.add_column("descricao")
        for t in loop.tool_registry.all():
            table.add_row(
                t.name,
                "sim" if t.destructive else "nao",
                t.description[:70],
            )
        console.print(table)
    finally:
        memory.close()


@app.command("audit")
def audit_cmd(
    limit: int = typer.Option(20, "--limit", "-n", help="Quantas entradas mostrar"),
    decision: str = typer.Option(None, "--decision", help="Filtrar por decisao (allow|deny|dry_run)"),
) -> None:
    """Mostra a trilha de auditoria."""
    cfg, memory, registry, router, loop = _bootstrap()
    try:
        if decision:
            rows = loop.authorizer.store.query(
                "SELECT * FROM audit WHERE decision = ? ORDER BY ts DESC LIMIT ?",
                (decision, limit),
            )
        else:
            rows = loop.authorizer.store.query(
                "SELECT * FROM audit ORDER BY ts DESC LIMIT ?",
                (limit,),
            )
        table = Table(title="Auditoria")
        table.add_column("ts")
        table.add_column("tool")
        table.add_column("decision")
        table.add_column("motivo")
        for r in rows:
            table.add_row(r["ts"][:19], r["tool"], r["decision"], (r["reason"] or "")[:60])
        console.print(table)
    finally:
        memory.close()


@app.command("sessions")
def sessions_cmd(
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Lista sessoes."""
    cfg, memory, registry, router, loop = _bootstrap()
    try:
        table = Table(title="Sessoes")
        table.add_column("id")
        table.add_column("created")
        table.add_column("updated")
        table.add_column("title")
        for s in memory.sessions.list(limit=limit):
            table.add_row(
                s["id"][:8],
                s["created_at"][:19],
                s["updated_at"][:19],
                (s.get("title") or "")[:40],
            )
        console.print(table)
    finally:
        memory.close()


if __name__ == "__main__":
    app()
