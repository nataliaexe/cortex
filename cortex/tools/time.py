"""Tools de tempo: timer, reminder, note.

Timers e reminders sao criados aqui mas disparados pelo scheduler
em background (cortex/scheduler/service.py). Notes sao persistidas
e buscaveis.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from cortex.tools.base import BaseTool, ToolContext, ToolResult


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_relative(text: str) -> timedelta | None:
    """Converte '5m', '2h', '30s', '1d', '1h30m' em timedelta."""
    text = text.strip().lower()
    if not text:
        return None

    pattern = re.compile(r"(\d+)\s*(s|seg|segundo|segundos|m|min|minuto|minutos|h|hora|horas|d|dia|dias)")
    matches = pattern.findall(text)
    if not matches:
        return None

    total = timedelta()
    for val, unit in matches:
        n = int(val)
        if unit in ("s", "seg", "segundo", "segundos"):
            total += timedelta(seconds=n)
        elif unit in ("m", "min", "minuto", "minutos"):
            total += timedelta(minutes=n)
        elif unit in ("h", "hora", "horas"):
            total += timedelta(hours=n)
        elif unit in ("d", "dia", "dias"):
            total += timedelta(days=n)
    return total if total.total_seconds() > 0 else None


def _parse_absolute(text: str) -> datetime | None:
    """Aceita varios formatos:
       '2026-09-15 14:00'
       '2026-09-15T14:00:00'
       '15/09/2026 14:00'
       'amanha 14:00'
       'hoje 14:00'
       'hoje 14h'
    """
    text = text.strip()
    t_low = text.lower()

    # amanha / hoje + hora
    m = re.match(r"^(amanha|amanhã|hoje)\s+(\d{1,2})[h:]?(\d{2})?", t_low)
    if m:
        when = m.group(1)
        hh = int(m.group(2))
        mm = int(m.group(3) or 0)
        base = _utc_now().replace(tzinfo=None).astimezone()
        if when.startswith("amanh"):
            base = base + timedelta(days=1)
        dt_local = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
        return dt_local.astimezone(timezone.utc)

    # formatos absolutos
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %Hh%M",
        "%Y-%m-%d %Hh%M",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.astimezone().astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _to_utc(text: str) -> datetime | None:
    """Tenta relativo primeiro, depois absoluto."""
    rel = _parse_relative(text)
    if rel is not None:
        return _utc_now() + rel

    # 'em 5m' / 'daqui 5m'
    m = re.match(r"^(?:em|daqui)\s+(.+)$", text.strip().lower())
    if m:
        rel = _parse_relative(m.group(1))
        if rel is not None:
            return _utc_now() + rel

    return _parse_absolute(text)


# ------------------------------------------------------------------
# Timer
# ------------------------------------------------------------------

class TimerSetTool(BaseTool):
    name = "timer.set"
    description = (
        "Cria um timer. Parametro 'when' aceita tempo relativo ('5m', '2h', '1h30m') "
        "ou absoluto ('hoje 14:00', '2026-09-15 14:30'). Opcional: label."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "when": {"type": "string", "description": "quando disparar"},
            "label": {"type": "string", "description": "descricao do timer"},
        },
        "required": ["when"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        when_str = args.get("when", "")
        fire_at = _to_utc(when_str)
        if fire_at is None:
            return ToolResult(ok=False, error=f"nao consegui interpretar o tempo: '{when_str}'")

        now = _utc_now()
        if fire_at <= now:
            return ToolResult(ok=False, error="o horario ja passou")

        tid = str(uuid.uuid4())
        label = args.get("label") or "timer"

        ctx.memory.store.execute(
            """
            INSERT INTO timers (id, label, fire_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (tid, label, fire_at.isoformat(), now.isoformat()),
        )

        delta = fire_at - now
        mins = int(delta.total_seconds() // 60)
        secs = int(delta.total_seconds() % 60)
        when_readable = f"em {mins}min {secs}s" if mins else f"em {secs}s"
        return ToolResult(
            ok=True,
            output=f"timer '{label}' definido para {when_readable} ({fire_at.isoformat()})",
            meta={"timer_id": tid, "fire_at": fire_at.isoformat()},
        )


class TimerListTool(BaseTool):
    name = "timer.list"
    description = "Lista timers ativos (nao disparados e nao cancelados)."
    destructive = False
    schema = {"type": "object", "properties": {}}

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        rows = ctx.memory.store.query(
            """
            SELECT id, label, fire_at, created_at
            FROM timers
            WHERE fired = 0 AND cancelled = 0
            ORDER BY fire_at ASC
            """
        )
        if not rows:
            return ToolResult(ok=True, output="nenhum timer ativo")

        now = _utc_now()
        lines = []
        for r in rows:
            try:
                fire = datetime.fromisoformat(r["fire_at"])
                delta = fire - now
                secs = int(delta.total_seconds())
                when = f"em {secs}s" if secs < 60 else f"em {secs // 60}min"
            except Exception:
                when = r["fire_at"]
            lines.append(f"  [{r['id'][:8]}] {r['label']} - {when}")
        return ToolResult(ok=True, output="\n".join(lines), meta={"count": len(rows)})


class TimerCancelTool(BaseTool):
    name = "timer.cancel"
    description = "Cancela um timer pelo id (prefixo)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {"timer_id": {"type": "string"}},
        "required": ["timer_id"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        tid = args.get("timer_id", "")
        rows = ctx.memory.store.query(
            "SELECT id, label FROM timers WHERE id LIKE ? AND fired = 0 AND cancelled = 0",
            (tid + "%",),
        )
        if not rows:
            return ToolResult(ok=False, error=f"timer '{tid}' nao encontrado")
        if len(rows) > 1:
            return ToolResult(ok=False, error=f"prefixo '{tid}' corresponde a {len(rows)} timers; seja mais especifico")

        real_id = rows[0]["id"]
        ctx.memory.store.execute("UPDATE timers SET cancelled = 1 WHERE id = ?", (real_id,))
        return ToolResult(ok=True, output=f"timer '{rows[0]['label']}' cancelado")


# ------------------------------------------------------------------
# Reminder
# ------------------------------------------------------------------

class ReminderSetTool(BaseTool):
    name = "reminder.set"
    description = (
        "Cria um lembrete. Parametros: title (obrigatorio), when (obrigatorio, "
        "aceita 'hoje 14:00', '5m', '2026-09-15 14:00'), description (opcional)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "when": {"type": "string"},
            "description": {"type": "string"},
        },
        "required": ["title", "when"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        title = args.get("title", "").strip()
        when_str = args.get("when", "")
        if not title:
            return ToolResult(ok=False, error="title obrigatorio")

        fire_at = _to_utc(when_str)
        if fire_at is None:
            return ToolResult(ok=False, error=f"nao consegui interpretar o tempo: '{when_str}'")

        now = _utc_now()
        if fire_at <= now:
            return ToolResult(ok=False, error="o horario ja passou")

        rid = str(uuid.uuid4())
        ctx.memory.store.execute(
            """
            INSERT INTO reminders (id, title, description, fire_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rid, title, args.get("description"), fire_at.isoformat(), now.isoformat()),
        )

        delta = fire_at - now
        mins = int(delta.total_seconds() // 60)
        when_readable = f"em {mins}min" if mins < 60 else f"em {mins // 60}h{(mins % 60)}min"
        return ToolResult(
            ok=True,
            output=f"lembrete '{title}' agendado {when_readable} ({fire_at.isoformat()})",
            meta={"reminder_id": rid, "fire_at": fire_at.isoformat()},
        )


class ReminderListTool(BaseTool):
    name = "reminder.list"
    description = "Lista lembretes ativos."
    destructive = False
    schema = {"type": "object", "properties": {}}

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        rows = ctx.memory.store.query(
            """
            SELECT id, title, fire_at
            FROM reminders
            WHERE fired = 0 AND cancelled = 0
            ORDER BY fire_at ASC
            """
        )
        if not rows:
            return ToolResult(ok=True, output="nenhum lembrete ativo")
        lines = []
        for r in rows:
            lines.append(f"  [{r['id'][:8]}] {r['title']} - {r['fire_at']}")
        return ToolResult(ok=True, output="\n".join(lines), meta={"count": len(rows)})


class ReminderCancelTool(BaseTool):
    name = "reminder.cancel"
    description = "Cancela um lembrete pelo id (prefixo)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {"reminder_id": {"type": "string"}},
        "required": ["reminder_id"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        rid = args.get("reminder_id", "")
        rows = ctx.memory.store.query(
            "SELECT id, title FROM reminders WHERE id LIKE ? AND fired = 0 AND cancelled = 0",
            (rid + "%",),
        )
        if not rows:
            return ToolResult(ok=False, error=f"lembrete '{rid}' nao encontrado")
        if len(rows) > 1:
            return ToolResult(ok=False, error=f"prefixo '{rid}' corresponde a {len(rows)} lembretes")
        real_id = rows[0]["id"]
        ctx.memory.store.execute("UPDATE reminders SET cancelled = 1 WHERE id = ?", (real_id,))
        return ToolResult(ok=True, output=f"lembrete '{rows[0]['title']}' cancelado")


# ------------------------------------------------------------------
# Note
# ------------------------------------------------------------------

class NoteAddTool(BaseTool):
    name = "note.add"
    description = "Adiciona uma nota rapida. Parametros: content (obrigatorio), title (opcional), tags (lista opcional)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "title": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["content"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        content = args.get("content", "").strip()
        if not content:
            return ToolResult(ok=False, error="content obrigatorio")

        nid = str(uuid.uuid4())
        now = _utc_now_iso()
        tags = ",".join(args.get("tags") or [])
        title = args.get("title") or content[:60]

        ctx.memory.store.execute(
            """
            INSERT INTO notes (id, title, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nid, title, content, tags, now, now),
        )
        return ToolResult(ok=True, output=f"nota criada: {title}", meta={"note_id": nid})


class NoteListTool(BaseTool):
    name = "note.list"
    description = "Lista notas. Opcional: limit (padrao 20), tag (filtro), search (busca em titulo/conteudo)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 20},
            "tag": {"type": "string"},
            "search": {"type": "string"},
        },
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        limit = int(args.get("limit", 20))
        tag = args.get("tag")
        search = args.get("search")

        sql = "SELECT id, title, content, tags, created_at FROM notes WHERE 1=1"
        params: list[Any] = []

        if tag:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        if search:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = ctx.memory.store.query(sql, params)
        if not rows:
            return ToolResult(ok=True, output="nenhuma nota encontrada")
        lines = []
        for r in rows:
            lines.append(f"  [{r['id'][:8]}] {r['title']}")
            if r["tags"]:
                lines.append(f"         tags: {r['tags']}")
        return ToolResult(ok=True, output="\n".join(lines), meta={"count": len(rows)})


class NoteSearchTool(BaseTool):
    name = "note.search"
    description = "Busca textual em notas (titulo e conteudo)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        q = args.get("query", "").strip()
        if not q:
            return ToolResult(ok=False, error="query obrigatoria")
        rows = ctx.memory.store.query(
            """
            SELECT id, title, content, tags, created_at
            FROM notes
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY updated_at DESC
            LIMIT 20
            """,
            (f"%{q}%", f"%{q}%"),
        )
        if not rows:
            return ToolResult(ok=True, output=f"nenhuma nota com '{q}'")
        lines = []
        for r in rows:
            preview = (r["content"] or "")[:120].replace("\n", " ")
            lines.append(f"  [{r['id'][:8]}] {r['title']}")
            lines.append(f"         {preview}")
        return ToolResult(ok=True, output="\n".join(lines), meta={"count": len(rows)})


class NoteDeleteTool(BaseTool):
    name = "note.delete"
    description = "Remove uma nota pelo id (prefixo)."
    destructive = True
    schema = {
        "type": "object",
        "properties": {"note_id": {"type": "string"}},
        "required": ["note_id"],
    }

    def preview(self, args: dict[str, Any]) -> Any:
        from cortex.governance.dry_run import DryRunPreview
        return DryRunPreview(
            tool=self.name,
            args=args,
            description=f"remover nota {args.get('note_id', '?')}",
            impact="irreversible",
        )

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        nid = args.get("note_id", "")
        rows = ctx.memory.store.query(
            "SELECT id, title FROM notes WHERE id LIKE ?", (nid + "%",)
        )
        if not rows:
            return ToolResult(ok=False, error=f"nota '{nid}' nao encontrada")
        if len(rows) > 1:
            return ToolResult(ok=False, error=f"prefixo '{nid}' corresponde a {len(rows)} notas")
        real_id = rows[0]["id"]
        ctx.memory.store.execute("DELETE FROM notes WHERE id = ?", (real_id,))
        return ToolResult(ok=True, output=f"nota '{rows[0]['title']}' removida")
