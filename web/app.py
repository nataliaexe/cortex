#!/usr/bin/env python3
"""FastAPI entry point for Cortex's local PWA and organized API."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ``python web/app.py`` sets sys.path to web/, while module imports live at
# project root. Keep both CLI and container entry points working.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.routes import chat, security, system, tasks
from api.services.policy_service import PolicyService
from core.governance import Governance
from database.connection import database_from_config
from database.repositories.audit_repository import AuditRepository
from database.repositories.conversation_repository import ConversationRepository
from database.repositories.scan_repository import ScanRepository
from database.repositories.task_repository import TaskRepository


class CortexWebApp:
    """HTTP boundary. Routes call services/repositories, never raw SQL."""
    def __init__(self, config: dict[str, Any]):
        self.logger, self.config = logging.getLogger(__name__), config
        settings = config.get("web", {})
        self.enabled = settings.get("enabled", True); self.host = settings.get("host", "127.0.0.1"); self.port = settings.get("port", 8000); self.debug = settings.get("debug", False)
        self.cortex_engine = None; self.active_connections: list[WebSocket] = []
        self.database = database_from_config(config); self.database.initialize()
        conversations = ConversationRepository(self.database); task_repository = TaskRepository(self.database); audit = AuditRepository(self.database); scans = ScanRepository(self.database)
        policy = PolicyService(Governance(config), task_repository, audit)
        self.app = FastAPI(title="Gênesis Córtex", description="IA local com execução governada e trilha de auditoria", version="1.1.0")
        self.app.add_middleware(CORSMiddleware, allow_origins=[f"http://{self.host}:{self.port}"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
        self.app.include_router(chat.router(conversations, lambda: self.cortex_engine))
        self.app.include_router(tasks.router(policy, task_repository))
        self.app.include_router(security.router(config, scans))
        self.app.include_router(system.router(config, audit, lambda: self.cortex_engine))
        self._setup_web_routes()
        self._setup_static_files()

    def _setup_web_routes(self) -> None:
        @self.app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root(request: Request):
            return Jinja2Templates(directory="web/templates").TemplateResponse("index.html", {"request": request})

        @self.app.get("/api/system/info", tags=["system"])
        async def system_info():
            from core.task_executor import TaskExecutor
            return json.loads(await TaskExecutor(self.config).get_system_info({}, {}))

        @self.app.get("/api/voice/status", tags=["voice"])
        async def voice_status():
            return {"enabled": self.config.get("voice", {}).get("enabled", False), "stt_available": False, "tts_available": False, "wake_word_available": False}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept(); self.active_connections.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    response = await self.cortex_engine.process_input(data) if self.cortex_engine else "Motor principal não conectado"
                    await websocket.send_json({"type": "response", "content": response})
            except WebSocketDisconnect:
                if websocket in self.active_connections: self.active_connections.remove(websocket)

    def _setup_static_files(self) -> None:
        static_dir = Path("web/static")
        if static_dir.exists(): self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def set_cortex_engine(self, engine) -> None: self.cortex_engine = engine
    def get_app(self) -> FastAPI: return self.app

    async def start(self):
        if not self.enabled: return False
        await uvicorn.Server(uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info" if self.debug else "warning")).serve()

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in self.active_connections.copy():
            try: await connection.send_json(message)
            except Exception: self.active_connections.remove(connection)


def create_web_app(config: dict[str, Any]) -> CortexWebApp: return CortexWebApp(config)


if __name__ == "__main__":
    import yaml
    with open("config.yaml", encoding="utf-8") as file: config = yaml.safe_load(file) or {}
    web_app = create_web_app(config)
    uvicorn.run(web_app.get_app(), host=web_app.host, port=web_app.port)
