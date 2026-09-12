"""Roda o scheduler standalone.

Uso: python -m cortex.scheduler
"""

from __future__ import annotations

import asyncio
import signal
import sys

from cortex.config import load_config
from cortex.memory.facade import Memory
from cortex.scheduler.service import SchedulerService
from cortex.utils.logging import configure_logging, get_logger

log = get_logger("scheduler")


async def main() -> None:
    cfg = load_config()
    configure_logging(cfg.app.log_file, cfg.app.log_level)

    memory = Memory(cfg.database.path)
    scheduler = SchedulerService(memory, check_interval=30.0, sound_enabled=True)

    stop_event = asyncio.Event()

    def _shutdown(signum, frame):
        log.info("scheduler_received_signal", signal=signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    await scheduler.start()
    log.info("scheduler_running_standalone")

    try:
        await stop_event.wait()
    finally:
        await scheduler.stop()
        memory.close()
        log.info("scheduler_exited")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
