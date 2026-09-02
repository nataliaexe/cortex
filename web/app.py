#!/usr/bin/env python3
"""
Gênesis Córtex - Web App PWA
Dashboard local com FastAPI
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio


class CortexWebApp:
    """Aplicação web PWA do Córtex"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.web_config = config.get("web", {})
        self.enabled = self.web_config.get("enabled", True)
        self.host = self.web_config.get("host", "127.0.0.1")
        self.port = self.web_config.get("port", 8000)
        self.debug = self.web_config.get("debug", False)
        
        # Motor principal (para integração)
        self.cortex_engine = None
        
        # WebSocket connections
        self.active_connections = []
        
        # Inicializa FastAPI
        self.app = FastAPI(
            title="Gênesis Córtex",
            description="Assistente Pessoal Offline",
            version="1.0.0"
        )
        
        # Configura middleware
        self._setup_middleware()
        
        # Configura rotas
        self._setup_routes()
        
        # Configura templates e static files
        self._setup_static_files()
        
    def _setup_middleware(self):
        """Configura middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_routes(self):
        """Configura rotas da API"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Página principal"""
            templates = Jinja2Templates(directory="web/templates")
            return templates.TemplateResponse("index.html", {"request": request})
            
        @self.app.get("/api/status")
        async def get_status():
            """Status do sistema"""
            if self.cortex_engine:
                return {
                    "status": "running",
                    "llm_enabled": self.cortex_engine.local_llm.enabled,
                    "voice_enabled": self.cortex_engine.config.get("voice", {}).get("enabled", False),
                    "security_enabled": self.cortex_engine.config.get("security", {}).get("scanner", {}).get("enabled", False)
                }
            return {"status": "standalone"}
            
        @self.app.post("/api/chat")
        async def chat(request: Request):
            """Endpoint de chat"""
            try:
                data = await request.json()
                user_input = data.get("message", "")
                
                if not user_input:
                    raise HTTPException(status_code=400, detail="Mensagem não fornecida")
                    
                if self.cortex_engine:
                    response = await self.cortex_engine.process_input(user_input)
                    return {"response": response}
                else:
                    return {"response": "Motor principal não conectado"}
                    
            except Exception as e:
                self.logger.error(f"Erro no chat: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/system/info")
        async def system_info():
            """Informações do sistema"""
            from core.task_executor import TaskExecutor
            executor = TaskExecutor(self.config)
            info = await executor.get_system_info({}, {})
            return json.loads(info)
            
        @self.app.get("/api/security/scan")
        async def security_scan(path: str = "."):
            """Scan de segurança"""
            from core.governance import Governance
            from security.universal_scanner import UniversalScanner
            target = Governance(self.config).ensure_path(path, must_exist=True)
            scanner = UniversalScanner(self.config)
            result = scanner.scan_directory(str(target)) if target.is_dir() else scanner.scan_file(str(target))
            return result
            
        @self.app.get("/api/security/dependencies")
        async def dependency_check(path: str = "."):
            """Verificação de dependências"""
            from core.governance import Governance
            from security.dependency_checker import DependencyChecker
            target = Governance(self.config).ensure_path(path, must_exist=True)
            checker = DependencyChecker(self.config)
            result = checker.check_directory(str(target))
            return result

        @self.app.get("/api/governance/status")
        async def governance_status():
            """Expõe a política ativa e o local do log de auditoria."""
            from core.governance import Governance
            return Governance(self.config).status()

        @self.app.get("/api/models/status")
        async def models_status():
            """Verifica os modelos Ollama sem baixá-los."""
            from core.local_llm import LocalLLM
            return await LocalLLM(self.config).model_status()
            
        @self.app.get("/api/voice/status")
        async def voice_status():
            """Status do sistema de voz"""
            return {
                "enabled": self.config.get("voice", {}).get("enabled", False),
                "stt_available": False,  # Seria verificado dinamicamente
                "tts_available": False,  # Seria verificado dinamicamente
                "wake_word_available": False  # Seria verificado dinamicamente
            }
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Endpoint WebSocket para comunicação em tempo real"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    
                    # Processa mensagem
                    if self.cortex_engine:
                        response = await self.cortex_engine.process_input(data)
                        await websocket.send_json({"type": "response", "content": response})
                    else:
                        await websocket.send_json({"type": "error", "content": "Motor não conectado"})
                        
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                
    def _setup_static_files(self):
        """Configura arquivos estáticos e templates"""
        # Monta diretório static
        static_dir = Path("web/static")
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            
        # Configura templates
        templates_dir = Path("web/templates")
        if templates_dir.exists():
            self.app.templates = Jinja2Templates(directory=str(templates_dir))
            
    def set_cortex_engine(self, engine):
        """Define motor principal para integração"""
        self.cortex_engine = engine
        
    async def start(self):
        """Inicia servidor web"""
        if not self.enabled:
            self.logger.info("Web app desabilitado")
            return False
            
        self.logger.info(f"Iniciando servidor web em {self.host}:{self.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info" if self.debug else "warning"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    async def broadcast(self, message: Dict[str, Any]):
        """Envia mensagem para todos os clientes WebSocket conectados"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.warning(f"Erro ao enviar para cliente: {e}")
                self.active_connections.remove(connection)
                
    def get_app(self):
        """Retorna aplicação FastAPI"""
        return self.app


def create_web_app(config: Dict[str, Any]) -> CortexWebApp:
    """Cria instância da aplicação web"""
    return CortexWebApp(config)


if __name__ == "__main__":
    import yaml
    
    # Carrega configuração
    try:
        with open("config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Erro ao carregar configuração: {e}")
        config = {}
        
    # Cria e inicia app
    web_app = create_web_app(config)
    uvicorn.run(web_app.get_app(), host="127.0.0.1", port=8000)
