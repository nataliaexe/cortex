"""Tools de calendario.

Duas camadas:
  1. Local (SQLite): funciona sempre, offline, sem configuracao.
  2. Google Calendar (opcional): sincroniza com eventos reais.

Toda operacao no local vai para a tabela calendar_events.
A sincronizacao com Google e feita por modulo separado
(cortex/tools/google_calendar.py).
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from cortex.governance.dry_run import DryRunPreview
from cortex.tools.base import BaseTool, ToolContext, ToolResult


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_when(text: str) -> datetime | None:
    """Aceita varios formatos para data/hora.
    'hoje 14:00', 'amanha 09:30', '2026-09-15 14:00', '15/09/2026 14:00', '14:00'
    """
    text = text.strip()
    t_low = text.lower()

    # hoje / amanha + hora
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

    # só hora: '14:00'
    m = re.match(r"^(\d{1,2})[h:]?(\d{2})?$", t_low)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2) or 0)
        base = _utc_now().replace(tzinfo=None).astimezone()
        dt_local = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
        # se já passou hoje, agenda pra amanhã
        if dt_local < datetime.now():
            dt_local = dt_local + timedelta(days=1)
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


def _parse_range(from_when: str, to_when: str | None) -> tuple[datetime, datetime] | None:
    """Interpreta um range de tempo.
    'hoje' -> hoje 00:00 ate amanha 00:00
    'amanha' -> amanha 00:00 ate depois
    'semana' -> agora ate +7 dias
    'YYYY-MM-DD' -> esse dia
    """
    t = from_when.strip().lower()
    base = _utc_now().replace(tzinfo=None).astimezone()

    if t == "hoje":
        start = base.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    if t in ("amanha", "amanhã"):
        start = base.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(days=1)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    if t == "semana":
        start = base.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    if t == "mes":
        start = base.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=30)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    # data especifica
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(from_when.strip(), fmt).astimezone()
            start = d.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
        except ValueError:
            continue

    # fallback: tenta parse_when para os dois
    start = _parse_when(from_when)
    if start is None:
        return None
    if to_when:
        end = _parse_when(to_when)
        if end is None:
            end = start + timedelta(hours=1)
    else:
        end = start + timedelta(hours=1)
    return start, end


# ------------------------------------------------------------------
# calendar.add
# ------------------------------------------------------------------

class CalendarAddTool(BaseTool):
    name = "calendar.add"
    description = (
        "Adiciona um evento ao calendario local. Parametros: "
        "title (obrigatorio), start (obrigatorio, ex: 'amanha 14:00'), "
        "end (opcional, se omitido assume 1h depois), "
        "description, location (opcionais)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "start": {"type": "string"},
            "end": {"type": "string"},
            "description": {"type": "string"},
            "location": {"type": "string"},
        },
        "required": ["title", "start"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        title = args.get("title", "").strip()
        if not title:
            return ToolResult(ok=False, error="title obrigatorio")

        start = _parse_when(args.get("start", ""))
        if start is None:
            return ToolResult(ok=False, error=f"nao entendi a data: '{args.get('start')}'")

        end_str = args.get("end")
        if end_str:
            end = _parse_when(end_str)
            if end is None:
                end = start + timedelta(hours=1)
        else:
            end = start + timedelta(hours=1)

        if end <= start:
            return ToolResult(ok=False, error="data final deve ser depois da inicial")

        eid = str(uuid.uuid4())
        now = _utc_now_iso()
        ctx.memory.store.execute(
            """
            INSERT INTO calendar_events
              (id, title, description, location, start_at, end_at, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'local', ?, ?)
            """,
            (
                eid,
                title,
                args.get("description"),
                args.get("location"),
                start.isoformat(),
                end.isoformat(),
                now,
                now,
            ),
        )

        return ToolResult(
            ok=True,
            output=f"evento '{title}' agendado para {start.isoformat()}",
            meta={"event_id": eid, "start": start.isoformat(), "end": end.isoformat()},
        )


# ------------------------------------------------------------------
# calendar.list
# ------------------------------------------------------------------

class CalendarListTool(BaseTool):
    name = "calendar.list"
    description = (
        "Lista eventos do calendario. Parametro 'range' aceita: "
        "'hoje', 'amanha', 'semana', 'mes', ou uma data especifica ('2026-09-15')."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "range": {"type": "string", "default": "hoje"},
            "limit": {"type": "integer", "default": 50},
        },
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        rng = args.get("range", "hoje")
        limit = int(args.get("limit", 50))

        parsed = _parse_range(rng, None)
        if parsed is None:
            return ToolResult(ok=False, error=f"range invalido: '{rng}'")
        start, end = parsed

        rows = ctx.memory.store.query(
            """
            SELECT id, title, description, location, start_at, end_at, all_day, source
            FROM calendar_events
            WHERE start_at >= ? AND start_at < ?
            ORDER BY start_at ASC
            LIMIT ?
            """,
            (start.isoformat(), end.isoformat(), limit),
        )

        if not rows:
            return ToolResult(ok=True, output=f"nenhum evento em '{rng}'")

        lines = [f"eventos em '{rng}':"]
        for r in rows:
            try:
                s = datetime.fromisoformat(r["start_at"]).astimezone()
                hh = s.strftime("%H:%M")
                dd = s.strftime("%d/%m")
            except Exception:
                hh = "?"
                dd = "?"
            loc = f" @ {r['location']}" if r["location"] else ""
            lines.append(f"  [{r['id'][:8]}] {dd} {hh} - {r['title']}{loc}")
        return ToolResult(ok=True, output="\n".join(lines), meta={"count": len(rows)})


# ------------------------------------------------------------------
# calendar.free
# ------------------------------------------------------------------

class CalendarFreeTool(BaseTool):
    name = "calendar.free"
    description = (
        "Encontra horarios livres em um range. Parametro 'range' aceita "
        "'hoje', 'amanha', 'semana'. Parametro 'duration' em minutos (padrao 60)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "range": {"type": "string", "default": "hoje"},
            "duration": {"type": "integer", "default": 60, "description": "minutos"},
            "work_start": {"type": "integer", "default": 8, "description": "hora inicial"},
            "work_end": {"type": "integer", "default": 22, "description": "hora final"},
        },
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        rng = args.get("range", "hoje")
        duration = int(args.get("duration", 60))
        work_start = int(args.get("work_start", 8))
        work_end = int(args.get("work_end", 22))

        parsed = _parse_range(rng, None)
        if parsed is None:
            return ToolResult(ok=False, error=f"range invalido: '{rng}'")
        range_start, range_end = parsed

        rows = ctx.memory.store.query(
            """
            SELECT start_at, end_at
            FROM calendar_events
            WHERE start_at >= ? AND start_at < ?
            ORDER BY start_at ASC
            """,
            (range_start.isoformat(), range_end.isoformat()),
        )

        # converte para lista de intervalos locais
        busy = []
        for r in rows:
            try:
                s = datetime.fromisoformat(r["start_at"])
                e = datetime.fromisoformat(r["end_at"])
                busy.append((s, e))
            except Exception:
                continue

        # gera slots livres por dia
        free_slots = []
        cur_day = range_start.replace(tzinfo=None)
        end_day = range_end.replace(tzinfo=None)

        while cur_day < end_day:
            day_start = cur_day.replace(hour=work_start, minute=0, second=0, microsecond=0)
            day_end = cur_day.replace(hour=work_end, minute=0, second=0, microsecond=0)
            day_start = day_start.astimezone(timezone.utc)
            day_end = day_end.astimezone(timezone.utc)

            # considera so busy dentro do dia
            day_busy = [(s, e) for (s, e) in busy if s < day_end and e > day_start]
            day_busy.sort()

            cursor = day_start
            for (bs, be) in day_busy:
                if bs > cursor:
                    gap = (bs - cursor).total_seconds() / 60
                    if gap >= duration:
                        free_slots.append((cursor, bs))
                cursor = max(cursor, be)

            if cursor < day_end:
                gap = (day_end - cursor).total_seconds() / 60
                if gap >= duration:
                    free_slots.append((cursor, day_end))

            cur_day = cur_day + timedelta(days=1)

        if not free_slots:
            return ToolResult(ok=True, output=f"nenhum slot livre de {duration}min em '{rng}'")

        lines = [f"slots livres em '{rng}' (>= {duration}min):"]
        for s, e in free_slots[:20]:
            sl = s.astimezone()
            el = e.astimezone()
            lines.append(f"  {sl.strftime('%d/%m %H:%M')} - {el.strftime('%H:%M')}  ({(e - s).total_seconds() / 60:.0f}min)")
        return ToolResult(ok=True, output="\n".join(lines), meta={"count": len(free_slots)})


# ------------------------------------------------------------------
# calendar.delete
# ------------------------------------------------------------------

class CalendarDeleteTool(BaseTool):
    name = "calendar.delete"
    description = "Remove um evento pelo id (prefixo)."
    destructive = True
    schema = {
        "type": "object",
        "properties": {"event_id": {"type": "string"}},
        "required": ["event_id"],
    }

    def preview(self, args: dict[str, Any]) -> DryRunPreview:
        return DryRunPreview(
            tool=self.name,
            args=args,
            description=f"remover evento {args.get('event_id', '?')}",
            impact="irreversible",
        )

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        eid = args.get("event_id", "")
        rows = ctx.memory.store.query(
            "SELECT id, title FROM calendar_events WHERE id LIKE ?", (eid + "%",)
        )
        if not rows:
            return ToolResult(ok=False, error=f"evento '{eid}' nao encontrado")
        if len(rows) > 1:
            return ToolResult(ok=False, error=f"prefixo '{eid}' corresponde a {len(rows)} eventos")
        real_id = rows[0]["id"]
        ctx.memory.store.execute("DELETE FROM calendar_events WHERE id = ?", (real_id,))
        return ToolResult(ok=True, output=f"evento '{rows[0]['title']}' removido")
