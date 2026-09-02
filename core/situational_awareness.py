#!/usr/bin/env python3
"""
Gênesis Córtex - Situational Awareness
Consciência situacional do contexto atual
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import psutil
import platform


class SituationalAwareness:
    """Módulo de consciência situacional"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.current_context = {}
        
    async def initialize(self):
        """Inicializa o módulo"""
        await self.update_context()
        self.logger.info("Situational Awareness inicializado")
        
    async def update_context(self):
        """Atualiza o contexto atual"""
        self.current_context = {
            "timestamp": datetime.now().isoformat(),
            "system": await self._get_system_context(),
            "user": await self._get_user_context(),
            "environment": await self._get_environment_context(),
            "resources": await self._get_resource_context()
        }
        
    async def analyze_context(self, user_input: str) -> Dict[str, Any]:
        """Analisa o contexto em relação à entrada do usuário"""
        await self.update_context()
        
        context_analysis = {
            "time_sensitive": self._is_time_sensitive(user_input),
            "resource_intensive": self._is_resource_intensive(user_input),
            "security_sensitive": self._is_security_sensitive(user_input),
            "network_required": self._is_network_required(user_input),
            "current_context": self.current_context
        }
        
        return context_analysis
        
    async def _get_system_context(self) -> Dict[str, Any]:
        """Obtém contexto do sistema"""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "uptime": self._get_uptime()
        }
        
    async def _get_user_context(self) -> Dict[str, Any]:
        """Obtém contexto do usuário"""
        try:
            import getpass
            return {
                "username": getpass.getuser(),
                "home_dir": str(Path.home()),
                "current_dir": str(Path.cwd())
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter contexto do usuário: {e}")
            return {}
            
    async def _get_environment_context(self) -> Dict[str, Any]:
        """Obtém contexto do ambiente"""
        import os
        return {
            "path": os.environ.get("PATH", ""),
            "shell": os.environ.get("SHELL", ""),
            "language": os.environ.get("LANG", ""),
            "display": os.environ.get("DISPLAY", "")
        }
        
    async def _get_resource_context(self) -> Dict[str, Any]:
        """Obtém contexto de recursos"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_available": disk.free
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter contexto de recursos: {e}")
            return {}
            
    def _get_uptime(self) -> str:
        """Obtém tempo de atividade do sistema"""
        try:
            uptime_seconds = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days}d {hours}h {minutes}m"
        except Exception:
            return "unknown"
            
    def _is_time_sensitive(self, user_input: str) -> bool:
        """Verifica se a entrada é sensível ao tempo"""
        time_keywords = ["agora", "hoje", "amanhã", "ontem", "hora", "minuto", "segundo", "timer", "alarme"]
        return any(keyword in user_input.lower() for keyword in time_keywords)
        
    def _is_resource_intensive(self, user_input: str) -> bool:
        """Verifica se a entrada requer muitos recursos"""
        resource_keywords = ["compilar", "analisar", "escanear", "processar", "treinar", "renderizar"]
        return any(keyword in user_input.lower() for keyword in resource_keywords)
        
    def _is_security_sensitive(self, user_input: str) -> bool:
        """Verifica se a entrada é sensível à segurança"""
        security_keywords = ["senha", "password", "chave", "key", "token", "segredo", "criptografar", "descriptografar"]
        return any(keyword in user_input.lower() for keyword in security_keywords)
        
    def _is_network_required(self, user_input: str) -> bool:
        """Verifica se a entrada requer rede"""
        network_keywords = ["baixar", "download", "upload", "conectar", "ping", "internet", "rede", "servidor"]
        return any(keyword in user_input.lower() for keyword in network_keywords)