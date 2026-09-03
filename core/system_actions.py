#!/usr/bin/env python3
"""
Gênesis Córtex - System Actions
Controle de ações do sistema operacional
"""

import logging
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
import platform


class SystemActions:
    """Ações de controle do sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.os_type = platform.system()
        
    async def set_volume(self, level: int) -> bool:
        """Define volume do sistema"""
        try:
            if self.os_type == "Linux":
                # Usa amixer para controle de volume
                subprocess.run(["amixer", "set", "Master", f"{level}%"], check=True)
                return True
            elif self.os_type == "Darwin":  # macOS
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
                return True
            elif self.os_type == "Windows":
                # Windows requer bibliotecas específicas
                self.logger.warning("Controle de volume no Windows não implementado")
                return False
            else:
                self.logger.warning(f"Sistema {self.os_type} não suportado para controle de volume")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao definir volume: {e}")
            return False
            
    async def get_volume(self) -> Optional[int]:
        """Obtém volume atual do sistema"""
        try:
            if self.os_type == "Linux":
                result = subprocess.run(
                    ["amixer", "get", "Master"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Parse do output para extrair porcentagem
                import re
                match = re.search(r'\[(\d+)%\]', result.stdout)
                if match:
                    return int(match.group(1))
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter volume: {e}")
            return None
            
    async def set_brightness(self, level: int) -> bool:
        """Define brilho da tela"""
        try:
            if self.os_type == "Linux":
                brightness_path = Path("/sys/class/backlight")
                if brightness_path.exists():
                    # Encontra primeiro dispositivo de backlight
                    for device in brightness_path.iterdir():
                        if device.is_dir():
                            max_brightness = int((device / "max_brightness").read_text())
                            brightness_value = int(max_brightness * (level / 100))
                            (device / "brightness").write_text(str(brightness_value))
                            return True
            elif self.os_type == "Darwin":
                subprocess.run(["brightness", str(level)], check=True)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao definir brilho: {e}")
            return False
            
    async def get_brightness(self) -> Optional[int]:
        """Obtém brilho atual da tela"""
        try:
            if self.os_type == "Linux":
                brightness_path = Path("/sys/class/backlight")
                if brightness_path.exists():
                    for device in brightness_path.iterdir():
                        if device.is_dir():
                            current = int((device / "brightness").read_text())
                            max_brightness = int((device / "max_brightness").read_text())
                            return int((current / max_brightness) * 100)
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter brilho: {e}")
            return None
            
    async def lock_screen(self) -> bool:
        """Bloqueia a tela"""
        try:
            if self.os_type == "Linux":
                subprocess.run(["xdg-screensaver", "lock"], check=True)
                return True
            elif self.os_type == "Darwin":
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"], check=True)
                return True
            elif self.os_type == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao bloquear tela: {e}")
            return False
            
    async def suspend_system(self) -> bool:
        """Suspende o sistema"""
        try:
            if self.os_type == "Linux":
                subprocess.run(["systemctl", "suspend"], check=True)
                return True
            elif self.os_type == "Darwin":
                subprocess.run(["pmset", "sleepnow"], check=True)
                return True
            elif self.os_type == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao suspender sistema: {e}")
            return False
            
    async def open_application(self, app_name: str) -> bool:
        """Abre uma aplicação"""
        try:
            if self.os_type == "Linux":
                subprocess.run(["xdg-open", app_name], check=True, shell=False)
                return True
            elif self.os_type == "Darwin":
                subprocess.run(["open", "-a", app_name], check=True, shell=False)
                return True
            elif self.os_type == "Windows":
                subprocess.run(["cmd", "/c", "start", "", app_name], check=True, shell=False)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao abrir aplicação: {e}")
            return False
            
    async def show_notification(self, title: str, message: str) -> bool:
        """Mostra notificação do sistema"""
        try:
            if self.os_type == "Linux":
                subprocess.run([
                    "notify-send",
                    title,
                    message
                ], check=True)
                return True
            elif self.os_type == "Darwin":
                subprocess.run([
                    "osascript",
                    "-e",
                    f'display notification "{message}" with title "{title}"'
                ], check=True)
                return True
            elif self.os_type == "Windows":
                # Windows requer bibliotecas específicas
                self.logger.warning("Notificações no Windows não implementadas")
                return False
            return False
        except Exception as e:
            self.logger.error(f"Erro ao mostrar notificação: {e}")
            return False
            
    async def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Executa comando do sistema - DEPRECATED: Use ComputerControl.run_command via TaskExecutor"""
        self.logger.warning("SystemActions.execute_command está depreciado. Use TaskExecutor.execute_command com ComputerControl")
        return {
            "success": False,
            "stdout": "",
            "stderr": "Método depreciado - use TaskExecutor.execute_command com argv",
            "returncode": -1
        }
            
    async def get_system_uptime(self) -> str:
        """Obtém tempo de atividade do sistema"""
        try:
            if self.os_type == "Linux":
                with open("/proc/uptime", "r") as f:
                    uptime_seconds = float(f.read().split()[0])
                    days = int(uptime_seconds // 86400)
                    hours = int((uptime_seconds % 86400) // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    return f"{days}d {hours}h {minutes}m"
            elif self.os_type == "Darwin":
                result = subprocess.run(["uptime"], capture_output=True, text=True)
                return result.stdout.strip()
            return "unknown"
        except Exception as e:
            self.logger.error(f"Erro ao obter uptime: {e}")
            return "unknown"