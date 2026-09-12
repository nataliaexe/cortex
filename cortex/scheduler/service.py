"""Scheduler em background.

Checa timers e reminders a cada N segundos. Quando vence, dispara
notificacao desktop + som (opcional), marca como fired.

Pode rodar:
  - Como task asyncio dentro do servidor (start_scheduler em lifespan).
  - Como processo standalone: `python -m cortex.scheduler`.
"""

from __future__ import annotations

import asyncio
import subprocess
from datetime import datetime, timezone
from typing import Any

from cortex.memory.facade import Memory
from cortex.utils.logging import get_logger

log = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _play_sound(kind: str = "normal") -> None:
    """Toca um som de aviso. kind pode ser 'normal', 'critical', 'reminder'."""
    candidates = [
        ("/usr/share/sounds/freedesktop/stereo/complete.oga", "paplay"),
        ("/usr/share/sounds/freedesktop/stereo/bell.oga", "paplay"),
        ("/usr/share/sounds/freedesktop/stereo/message.oga", "paplay"),
        ("/usr/share/sounds/alsa/Front_Center.wav", "aplay"),
    ]
    for path, player in candidates:
        try:
            import os
            if os.path.exists(path):
                subprocess.run(
                    [player, path],
                    timeout=5,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        except Exception:
            continue


def _notify(title: str, body: str = "", urgency: str = "normal") -> None:
    """Envia notificacao desktop via notify-send."""
    try:
        argv = ["notify-send", "-u", urgency, "-a", "Cortex", title]
        if body:
            argv.append(body)
        subprocess.run(argv, timeout=5, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log.warning("notify_failed", error=str(e))


class SchedulerService:
    """Loop que dispara timers e reminders vencidos."""

    def __init__(
        self,
        memory: Memory,
        check_interval: float = 30.0,
        sound_enabled: bool = True,
    ) -> None:
        self.memory = memory
        self.check_interval = check_interval
        self.sound_enabled = sound_enabled
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        log.info("scheduler_started", interval_s=self.check_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        log.info("scheduler_stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as e:
                log.error("scheduler_tick_failed", error=str(e))
            await asyncio.sleep(self.check_interval)

    async def _tick(self) -> None:
        now_iso = _utc_now_iso()

        timers = self.memory.store.query(
            """
            SELECT id, label, fire_at FROM timers
            WHERE fired = 0 AND cancelled = 0 AND fire_at <= ?
            """,
            (now_iso,),
        )
        for t in timers:
            label = t["label"] or "timer"
            self._fire_timer(t["id"], label)

        reminders = self.memory.store.query(
            """
            SELECT id, title, description FROM reminders
            WHERE fired = 0 AND cancelled = 0 AND fire_at <= ?
            """,
            (now_iso,),
        )
        for r in reminders:
            self._fire_reminder(r["id"], r["title"], r["description"])

    def _fire_timer(self, timer_id: str, label: str) -> None:
        self.memory.store.execute(
            "UPDATE timers SET fired = 1 WHERE id = ? AND fired = 0",
            (timer_id,),
        )
        log.info("timer_fired", id=timer_id, label=label)
        _notify("Cortex - timer", label, urgency="normal")
        if self.sound_enabled:
            _play_sound("normal")

    def _fire_reminder(self, reminder_id: str, title: str, description: str | None) -> None:
        self.memory.store.execute(
            "UPDATE reminders SET fired = 1 WHERE id = ? AND fired = 0",
            (reminder_id,),
        )
        log.info("reminder_fired", id=reminder_id, title=title)
        body = title
        if description:
            body = f"{title} - {description}"
        _notify("Cortex - lembrete", body, urgency="critical")
        if self.sound_enabled:
            _play_sound("reminder")


_service: SchedulerService | None = None


async def start_scheduler(memory: Memory, **kwargs: Any) -> SchedulerService:
    global _service
    if _service is None:
        _service = SchedulerService(memory, **kwargs)
    await _service.start()
    return _service


async def stop_scheduler() -> None:
    global _service
    if _service is not None:
        await _service.stop()
        _service = None
