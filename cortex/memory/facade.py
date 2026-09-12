"""Fachada de memoria: um ponto de entrada para o nucleo."""

from __future__ import annotations

from pathlib import Path

from cortex.memory.episodic import EpisodicMemory
from cortex.memory.events_repo import EventsRepo
from cortex.memory.semantic import SemanticMemory
from cortex.memory.embeddings import EmbeddingStore
from cortex.memory.projects import ProjectsRepo
from cortex.memory.sources import SourcesRepo
from cortex.memory.sessions_repo import SessionsRepo
from cortex.memory.store import Store
from cortex.memory.working import WorkingMemory
from cortex.models.local import LocalClient


class Memory:
    """Fachada unica de memoria. Toda persistencia passa por aqui."""

    def __init__(self, db_path: str | Path) -> None:
        self.store = Store(db_path)
        self.events = EventsRepo(self.store)
        self.sessions = SessionsRepo(self.store)
        self.projects = ProjectsRepo(self.store)
        self.episodic = EpisodicMemory(self.store)
        self.semantic = SemanticMemory(self.store)
        self.working = WorkingMemory(self.store)
        self.embeddings = EmbeddingStore(self.store)
        # SourcesRepo precisa de um LocalClient. Passamos um novo (leve) aqui.
        # O loop pode passar o mesmo client depois; por ora um proprio serve.
        from cortex.config import load_config as _lc
        _cfg = _lc()
        self._local_for_sources = LocalClient(_cfg.models.local)
        self.sources = SourcesRepo(self.store, self.embeddings, self._local_for_sources)

    def close(self) -> None:
        self.store.close()
