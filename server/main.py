"""Servidor FastAPI do Cortex.

Expõe o nucleo cognitivo via HTTP. Usado pelo CLI, pela UI web
e por qualquer outro cliente futuro.

Startup: init_state() cria Memory, Registry, Router, Loop.
Shutdown: shutdown_state() fecha as conexoes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.deps import get_state, init_state, shutdown_state
from server.routes import chat, health, projects, providers, sessions, sources
from cortex.utils.logging import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("server_starting")
    state = init_state()

    # inicia o scheduler em background
    from cortex.scheduler.service import start_scheduler, stop_scheduler
    await start_scheduler(state.memory, check_interval=30.0, sound_enabled=True)

    yield

    log.info("server_shutting_down")
    await stop_scheduler()
    shutdown_state()


app = FastAPI(
    title="Cortex",
    description="Assistente pessoal hibrido, governado e offline-first.",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS para o frontend em dev (Vite roda em 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# rotas
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(projects.router)
app.include_router(sessions.router)
app.include_router(sources.router)
app.include_router(providers.router)


@app.get("/")
async def root():
    return {
        "name": "Cortex",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
    }
