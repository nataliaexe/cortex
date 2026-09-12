"""Fachada de memoria: um ponto de entrada para o nucleo."""

from __future__ import annotations

from pathlib import Path

from cortex.memory.episodic import EpisodicMemory
from cortex.memory.events_repo import EventsRepo
from cortex.memory.semantic import SemanticMemory
from cortex.memory.sessions_repo import SessionsRepo
from cortex.memory.store import Store
from cortex.memory.working import WorkingMemory


class Memory:
    """Fachada unica de memoria. Toda persistencia passa por aqui."""

    def __init__(self, db_path: str | Path) -> None:
        self.store = Store(db_path)
        self.events = EventsRepo(self.store)
        self.sessions = SessionsRepo(self.store)
        self.episodic = EpisodicMemory(self.store)
        self.semantic = SemanticMemory(self.store)
        self.working = WorkingMemory(self.store)

    def close(self) -> None:
        self.store.close()
