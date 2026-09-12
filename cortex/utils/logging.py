"""Logging estruturado do Cortex. JSONL auditavel + stdout legivel."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog


def _ensure_log_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def configure_logging(log_file: str | Path = "logs/cortex.log", level: str = "info") -> None:
    """Configura structlog com dois sinks: console legivel e arquivo JSONL."""
    log_path = Path(log_file).expanduser()
    _ensure_log_dir(log_path)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Retorna um logger estruturado."""
    return structlog.get_logger(name)
