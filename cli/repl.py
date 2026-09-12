"""REPL interativo do Cortex."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown

from cortex.nucleus.loop import CortexLoop

console = Console()

REPL_STYLE = Style.from_dict({
    "prompt": "ansicyan bold",
    "session": "ansigray",
})

HELP_TEXT = """\
[bold]Comandos do REPL:[/bold]
  :help          esta ajuda
  :quit / :q     sair
  :new           nova sessao
  :sessions      lista sessoes
  :tools         lista tools
  :providers     lista providers
  :audit [n]     ultimas n entradas de auditoria
  :memory        mostra working memory atual
  :auto on|off   liga/desliga auto-confirm de dry-runs
  :mode          lista modos de interacao
  :mode <nome>   muda o modo (default, english)

[bold]Uso normal:[/bold]
  digite sua mensagem e Enter. Ctrl+C cancela. Ctrl+D sai.
"""


def _print_banner() -> None:
    console.print()
    console.print("[bold cyan]Cortex[/bold cyan] [dim]v0.1.0[/dim]")
    console.print("[dim]Digite[/dim] [cyan]:help[/cyan] [dim]para comandos.[/dim]")
    console.print()


async def _handle_meta_command(line: str, state: dict[str, Any], loop: CortexLoop) -> bool:
    """Trata comando ':' do REPL. Retorna True se tratado."""
    parts = line.strip().split()
    cmd = parts[0].lower()

    if cmd in (":quit", ":q", ":exit"):
        console.print("[dim]ate logo.[/dim]")
        return True

    if cmd == ":help":
        console.print(HELP_TEXT)
        return True

    if cmd == ":new":
        sid = loop.memory.sessions.create(title="repl")
        state["session_id"] = sid
        console.print(f"[dim]nova sessao:[/dim] [cyan]{sid[:8]}[/cyan]")
        return True

    if cmd == ":sessions":
        for s in loop.memory.sessions.list(limit=20):
            console.print(f"  [cyan]{s['id'][:8]}[/cyan] {s['updated_at'][:19]} {(s.get('title') or '')[:40]}")
        return True

    if cmd == ":tools":
        for t in loop.tool_registry.all():
            flag = "[red]DESTRUTIVA[/red]" if t.destructive else "[green]segura[/green]"
            console.print(f"  {flag} [cyan]{t.name}[/cyan] - {t.description[:60]}")
        return True

    if cmd == ":providers":
        for s in loop.registry.status():
            flag = "[green]OK[/green]" if s.available else "[red]X[/red]"
            console.print(f"  {flag} [cyan]{s.name}[/cyan] {s.reason or ''}")
        return True

    if cmd == ":audit":
        n = 10
        if len(parts) > 1 and parts[1].isdigit():
            n = int(parts[1])
        rows = loop.authorizer.store.query(
            "SELECT * FROM audit ORDER BY ts DESC LIMIT ?", (n,)
        )
        for r in rows:
            console.print(f"  [dim]{r['ts'][:19]}[/dim] [cyan]{r['tool']}[/cyan] {r['decision']} {(r['reason'] or '')[:50]}")
        return True

    if cmd == ":memory":
        w = loop.memory.working.get(state["session_id"])
        console.print_json(data=w)
        return True

    if cmd == ":mode":
        if len(parts) > 1:
            from cortex.nucleus.modes import MODES
            nome = parts[1].lower()
            if nome in MODES:
                state["mode"] = nome
                console.print(f"[dim]modo:[/dim] [cyan]{nome}[/cyan] - {MODES[nome].description}")
            else:
                console.print(f"[yellow]modo desconhecido: {nome}. disponiveis: {', '.join(MODES.keys())}[/yellow]")
        else:
            from cortex.nucleus.modes import MODES
            console.print(f"[dim]modo atual:[/dim] [cyan]{state.get('mode', 'default')}[/cyan]")
            for name, m in MODES.items():
                console.print(f"  [cyan]{name}[/cyan] - {m.description}")
        return True

    if cmd == ":auto":
        if len(parts) > 1:
            state["auto_confirm"] = parts[1].lower() == "on"
        console.print(f"[dim]auto_confirm = {state['auto_confirm']}[/dim]")
        return True

    if cmd.startswith(":"):
        console.print(f"[yellow]comando desconhecido: {cmd}[/yellow]")
        return True

    return False


async def run_repl(loop: CortexLoop) -> None:
    """Loop principal do REPL."""
    history_path = loop.cfg.database.path.replace("cortex.db", ".repl_history")
    session: PromptSession = PromptSession(history=FileHistory(history_path), style=REPL_STYLE)

    sid = loop.memory.sessions.create(title="repl")
    state: dict[str, Any] = {"session_id": sid, "auto_confirm": False, "mode": "default"}

    _print_banner()
    console.print(f"[dim]sessao:[/dim] [cyan]{sid[:8]}[/cyan]\n")

    while True:
        try:
            prompt_text = [
                ("class:prompt", "cortex"),
                ("class:session", f" [{state['session_id'][:8]}]"),
                ("class:prompt", " > "),
            ]
            line = await session.prompt_async(prompt_text)
        except KeyboardInterrupt:
            console.print()
            continue
        except EOFError:
            console.print("[dim]ate logo.[/dim]")
            break

        line = line.strip()
        if not line:
            continue

        if line.startswith(":"):
            done = await _handle_meta_command(line, state, loop)
            if line.split()[0] in (":quit", ":q", ":exit") and done:
                break
            continue

        # mensagem normal
        try:
            result = await loop.run_turn(
                state["session_id"],
                line,
                auto_confirm=state["auto_confirm"],
                mode=state.get("mode", "default"),
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]turno cancelado pelo usuario[/yellow]")
            continue
        except asyncio.CancelledError:
            console.print("\n[yellow]turno cancelado[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]erro no turno: {type(e).__name__}: {e}[/red]")
            continue

        # aviso de multi-intent
        if result.was_multi_intent:
            console.print(f"[dim]multi-intent:[/dim] [yellow]{len(result.subtasks)} tarefas detectadas[/yellow]")

        # imprime plano se houver
        if result.plan and result.plan.steps:
            console.print("[dim]plano:[/dim]")
            for i, s in enumerate(result.plan.steps, 1):
                mark = "[green]v[/green]" if s.done else "[yellow].[/yellow]"
                tool_info = f" [cyan]{s.tool}[/cyan]" if s.tool else ""
                console.print(f"  {mark} {i}. {s.description}{tool_info}")
            console.print()

        # imprime tools executadas
        if result.tool_calls:
            for tc in result.tool_calls:
                flag = "[green]OK[/green]" if tc["ok"] else "[red]FAIL[/red]"
                console.print(f"[dim]tool[/dim] {flag} [cyan]{tc['tool']}[/cyan]")
                if tc["output"]:
                    preview = tc["output"].strip()[:300]
                    console.print(f"[dim]{preview}[/dim]")
                if tc["error"]:
                    console.print(f"[red]{tc['error'][:200]}[/red]")
            console.print()

        # dry-runs pendentes
        if result.dry_runs_pending:
            console.print("[yellow]dry-runs pendentes (nao executados):[/yellow]")
            for p in result.dry_runs_pending:
                console.print(f"  [cyan]{p.tool}[/cyan] impacto={p.impact}")
                console.print(f"    {p.description}")
                if p.diff:
                    console.print(f"    [dim]{p.diff[:200]}[/dim]")
            console.print()

        # resposta final
        try:
            console.print(Markdown(result.final_text))
        except Exception:
            console.print(result.final_text)

        console.print(
            f"[dim]({result.provider}:{result.model})[/dim]"
        )
        console.print()
