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


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="host do servidor"),
    port: int = typer.Option(8765, "--port", "-p", help="porta do servidor"),
    reload: bool = typer.Option(False, "--reload", help="recarrega automaticamente em dev"),
) -> None:
    """Sobe o servidor HTTP do Cortex (FastAPI + uvicorn)."""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]uvicorn nao instalado. Rode: pip install 'uvicorn[standard]'[/red]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Cortex server[/cyan] em [bold]http://{host}:{port}[/bold]")
    console.print(f"[dim]docs:[/dim] [cyan]http://{host}:{port}/docs[/cyan]")
    console.print("[dim]Ctrl+C para parar[/dim]")
    console.print()

    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


calendar_app = typer.Typer(help="Comandos de calendario (local + Google).", no_args_is_help=True)
app.add_typer(calendar_app, name="calendar")


@calendar_app.command("auth")
def calendar_auth() -> None:
    """Autentica no Google Calendar (abre navegador na primeira vez)."""
    from cortex.tools.google_calendar import GoogleCalendarClient, GoogleCalendarNotConfigured

    client = GoogleCalendarClient()
    if not client.is_configured():
        console.print("[red]credenciais nao encontradas em data/google_credentials.json[/red]")
        raise typer.Exit(code=1)

    console.print("[cyan]Abrindo navegador para autorizar...[/cyan]")
    try:
        # forca fluxo interativo
        client._load_credentials(allow_interactive=True)
        console.print("[green]Autorizado. Token salvo em data/google_token.json[/green]")
    except Exception as e:
        console.print(f"[red]erro: {type(e).__name__}: {e}[/red]")
        raise typer.Exit(code=1)


@calendar_app.command("status")
def calendar_status() -> None:
    """Mostra o status do calendario (local + Google)."""
    from cortex.config import load_config
    from cortex.memory.facade import Memory
    from cortex.tools.google_calendar import GoogleCalendarClient

    cfg = load_config()
    mem = Memory(cfg.database.path)

    try:
        local_count = mem.store.query_one("SELECT COUNT(*) AS n FROM calendar_events")["n"]
    except Exception:
        local_count = 0

    console.print(f"[cyan]Eventos locais:[/cyan] {local_count}")

    gc = GoogleCalendarClient()
    if not gc.is_configured():
        console.print("[yellow]Google: nao configurado (falta data/google_credentials.json)[/yellow]")
    elif not gc.has_token():
        console.print("[yellow]Google: configurado, mas sem token. Rode `cortex calendar auth`[/yellow]")
    else:
        console.print("[green]Google: autenticado[/green]")

    mem.close()


@calendar_app.command("sync")
def calendar_sync(
    days_ahead: int = typer.Option(30, "--days", "-d", help="quantos dias buscar"),
) -> None:
    """Sincroniza eventos do Google para o banco local."""
    import asyncio
    from datetime import datetime, timedelta, timezone

    from cortex.config import load_config
    from cortex.memory.facade import Memory
    from cortex.tools.google_calendar import GoogleCalendarClient

    cfg = load_config()
    mem = Memory(cfg.database.path)

    gc = GoogleCalendarClient()
    if not gc.has_token():
        console.print("[red]sem token Google. Rode `cortex calendar auth` primeiro.[/red]")
        mem.close()
        raise typer.Exit(code=1)

    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    try:
        events = gc.list_events(time_min=now, time_max=end, max_results=250)
    except Exception as e:
        console.print(f"[red]erro ao listar: {type(e).__name__}: {e}[/red]")
        mem.close()
        raise typer.Exit(code=1)

    inserted = 0
    updated = 0
    for ev in events:
        # verifica se ja existe por (source=google, external_id=ev.id)
        existing = mem.store.query_one(
            "SELECT id FROM calendar_events WHERE source = 'google' AND external_id = ?",
            (ev.id,),
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        if existing:
            mem.store.execute(
                """
                UPDATE calendar_events
                SET title = ?, description = ?, location = ?, start_at = ?, end_at = ?, all_day = ?, updated_at = ?
                WHERE id = ?
                """,
                (ev.summary, ev.description, ev.location, ev.start_iso, ev.end_iso, 1 if ev.all_day else 0, now_iso, existing["id"]),
            )
            updated += 1
        else:
            import uuid
            mem.store.execute(
                """
                INSERT INTO calendar_events
                  (id, title, description, location, start_at, end_at, all_day, source, external_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'google', ?, ?, ?)
                """,
                (str(uuid.uuid4()), ev.summary, ev.description, ev.location, ev.start_iso, ev.end_iso, 1 if ev.all_day else 0, ev.id, now_iso, now_iso),
            )
            inserted += 1

    console.print(f"[green]Sincronizados {len(events)} eventos: {inserted} novos, {updated} atualizados[/green]")
    mem.close()


@app.command()
def scheduler() -> None:
    """Roda o scheduler em foreground (dispara timers e reminders)."""
    import asyncio
    from cortex.scheduler.service import SchedulerService

    cfg, memory, registry, router, loop = _bootstrap()

    async def _run():
        sched = SchedulerService(memory, check_interval=30.0, sound_enabled=True)
        await sched.start()
        console.print("[cyan]Scheduler rodando. Ctrl+C para parar.[/cyan]")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await sched.stop()
            memory.close()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print()
        console.print("[dim]scheduler parado[/dim]")


@app.command()
def doctor() -> None:
    """Diagnostico rapido: providers, tools, memoria, calendario."""
    from cortex.tools.google_calendar import GoogleCalendarClient
    from rich.table import Table

    cfg, memory, registry, router, loop = _bootstrap()

    console.print("[bold cyan]Cortex - diagnostico[/bold cyan]")
    console.print(f"[dim]versao:[/dim] {cfg.app.version}")
    console.print()

    # providers
    console.print("[bold]Providers[/bold]")
    table = Table(show_header=False, box=None)
    for s in registry.status():
        flag = "[green]OK[/green]" if s.available else "[red]X [/red]"
        table.add_row(flag, s.name, s.reason or "")
    console.print(table)
    console.print()

    # tools
    tools = loop.tool_registry.all()
    console.print(f"[bold]Tools registradas:[/bold] {len(tools)}")
    for t in tools:
        mark = "[red]D[/red]" if t.destructive else "[green]S[/green]"
        console.print(f"  {mark} {t.name}")
    console.print()

    # memoria
    try:
        sessions = len(memory.sessions.list(limit=1000))
        projects = len(memory.projects.list(limit=1000))
        console.print(f"[bold]Memoria:[/bold] {sessions} sessoes, {projects} projetos")
    except Exception as e:
        console.print(f"[red]memoria com erro: {e}[/red]")

    # calendario
    gc = GoogleCalendarClient()
    if not gc.is_configured():
        console.print("[bold]Google Calendar:[/bold] [dim]nao configurado[/dim]")
    elif not gc.has_token():
        console.print("[bold]Google Calendar:[/bold] [yellow]configurado, sem token. Rode `cortex calendar auth`[/yellow]")
    else:
        console.print("[bold]Google Calendar:[/bold] [green]autenticado[/green]")

    # timers/reminders ativos
    timers = memory.store.query(
        "SELECT COUNT(*) AS n FROM timers WHERE fired = 0 AND cancelled = 0"
    )[0]["n"]
    reminders = memory.store.query(
        "SELECT COUNT(*) AS n FROM reminders WHERE fired = 0 AND cancelled = 0"
    )[0]["n"]
    console.print(f"[bold]Agendamentos ativos:[/bold] {timers} timers, {reminders} reminders")

    memory.close()


if __name__ == "__main__":
    app()
