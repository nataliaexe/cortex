"""Dependencias compartilhadas do servidor.

O CortexLoop, Memory e ModelRegistry sao inicializados UMA VEZ
no startup da aplicacao e reusados por todas as requests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cortex.config import CortexConfig, load_config
from cortex.memory.facade import Memory
from cortex.models.registry import ModelRegistry
from cortex.nucleus.loop import CortexLoop
from cortex.nucleus.router import Router
from cortex.tools.registry import register_defaults
from cortex.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


@dataclass
class AppState:
    cfg: CortexConfig
    memory: Memory
    registry: ModelRegistry
    router: Router
    loop: CortexLoop


_state: AppState | None = None


def init_state() -> AppState:
    """Inicializa o estado global do servidor. Chamado no startup."""
    global _state
    if _state is not None:
        return _state

    cfg = load_config()
    configure_logging(cfg.app.log_file, cfg.app.log_level)

    memory = Memory(cfg.database.path)
    registry = ModelRegistry(cfg)
    router = Router(cfg, registry)
    register_defaults()
    loop = CortexLoop(cfg, memory, registry, router)

    _state = AppState(
        cfg=cfg,
        memory=memory,
        registry=registry,
        router=router,
        loop=loop,
    )
    log.info("server_state_initialized", version=cfg.app.version)
    return _state


def get_state() -> AppState:
    if _state is None:
        raise RuntimeError("estado nao inicializado; chame init_state() no startup")
    return _state


def shutdown_state() -> None:
    global _state
    if _state is not None:
        _state.memory.close()
        _state = None
