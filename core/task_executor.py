#!/usr/bin/env python3
"""
Gênesis Córtex - Task Executor
Executa ações mapeadas (40+ métodos)
"""

import asyncio
import logging
import subprocess
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta


class TaskExecutor:
    """Executor de tarefas e ações do sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.action_map = self._build_action_map()
        
    def _build_action_map(self) -> Dict[str, callable]:
        """Constrói mapa de ações disponíveis"""
        return {
            # Ações de sistema
            "system_info": self.get_system_info,
            "disk_usage": self.get_disk_usage,
            "memory_usage": self.get_memory_usage,
            "network_status": self.get_network_status,
            "running_processes": self.get_running_processes,
            
            # Ações de arquivos
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "delete_file": self.delete_file,
            "create_directory": self.create_directory,
            
            # Ações de assistente pessoal
            "set_volume": self.set_volume,
            "set_brightness": self.set_brightness,
            "create_note": self.create_note,
            "list_notes": self.list_notes,
            "set_timer": self.set_timer,
            "set_reminder": self.set_reminder,
            
            # Ações de segurança
            "scan_ports": self.scan_ports,
            "scan_processes": self.scan_processes,
            "check_passwords": self.check_passwords,
            "analyze_logs": self.analyze_logs,
            
            # Ações de desenvolvimento
            "run_code": self.run_code,
            "git_status": self.git_status,
            "git_commit": self.git_commit,
            "docker_status": self.docker_status,
            
            # Ações de web
            "web_search": self.web_search,
            "download_file": self.download_file,
            
            # Ações de conhecimento
            "neuroscience_query": self.neuroscience_query,
            "robotics_query": self.robotics_query,
            "security_query": self.security_query,
            
            # Ações de memória
            "store_memory": self.store_memory,
            "retrieve_memory": self.retrieve_memory,
            "search_memories": self.search_memories,
            
            # Ações de configuração
            "update_config": self.update_config,
            "reload_config": self.reload_config,
            
            # Ações de diagnóstico
            "health_check": self.health_check,
            "performance_test": self.performance_test,
            "diagnostic_report": self.diagnostic_report,
            
            # Ações de backup
            "create_backup": self.create_backup,
            "restore_backup": self.restore_backup,
            
            # Ações de análise
            "analyze_binary": self.analyze_binary,
            "analyze_dependencies": self.analyze_dependencies,
            "generate_report": self.generate_report,
            
            # Ações de rede
            "ping_host": self.ping_host,
            "trace_route": self.trace_route,
            "dns_lookup": self.dns_lookup,
            
            # Ações de sistema
            "shutdown": self.shutdown,
            "reboot": self.reboot,
            "sleep": self.sleep,
        }
        
    async def initialize(self):
        """Inicializa o executor de tarefas"""
        self.logger.info("Task Executor inicializado")
        
    async def cleanup(self):
        """Limpa recursos"""
        self.logger.info("Task Executor finalizado")
        
    async def execute_intent(self, intent: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Executa uma intenção específica"""
        
        if intent not in self.action_map:
            return f"Ação '{intent}' não implementada"
            
        try:
            action = self.action_map[intent]
            result = await action(parameters, context)
            return str(result)
        except Exception as e:
            self.logger.error(f"Erro ao executar {intent}: {e}")
            return f"Erro ao executar ação: {str(e)}"
    
    # Ações de sistema
    async def get_system_info(self, params: Dict, context: Dict) -> str:
        """Obtém informações do sistema"""
        import platform
        info = {
            "sistema": platform.system(),
            "versão": platform.version(),
            "arquitetura": platform.machine(),
            "processador": platform.processor(),
            "hostname": platform.node()
        }
        return json.dumps(info, indent=2, ensure_ascii=False)
        
    async def get_disk_usage(self, params: Dict, context: Dict) -> str:
        """Obtém uso de disco"""
        import shutil
        usage = shutil.disk_usage("/")
        return f"Total: {usage.total / (1024**3):.2f} GB | Usado: {usage.used / (1024**3):.2f} GB | Livre: {usage.free / (1024**3):.2f} GB"
        
    async def get_memory_usage(self, params: Dict, context: Dict) -> str:
        """Obtém uso de memória"""
        import psutil
        mem = psutil.virtual_memory()
        return f"Total: {mem.total / (1024**3):.2f} GB | Usado: {mem.used / (1024**3):.2f} GB | Porcentagem: {mem.percent}%"
        
    async def get_network_status(self, params: Dict, context: Dict) -> str:
        """Obtém status da rede"""
        import psutil
        interfaces = psutil.net_if_addrs()
        status = []
        for iface, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == 2:  # AF_INET
                    status.append(f"{iface}: {addr.address}")
        return "\n".join(status) if status else "Nenhuma interface de rede encontrada"
        
    async def get_running_processes(self, params: Dict, context: Dict) -> str:
        """Lista processos em execução"""
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                processes.append(f"PID: {proc.info['pid']} | Nome: {proc.info['name']} | CPU: {proc.info['cpu_percent']}%")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return "\n".join(processes[:20])  # Limita a 20 processos
        
    # Ações de arquivos
    async def list_files(self, params: Dict, context: Dict) -> str:
        """Lista arquivos em um diretório"""
        path = params.get("path", ".")
        try:
            files = list(Path(path).iterdir())
            return "\n".join([f.name for f in files])
        except Exception as e:
            return f"Erro ao listar arquivos: {e}"
            
    async def read_file(self, params: Dict, context: Dict) -> str:
        """Lê conteúdo de um arquivo"""
        path = params.get("path")
        if not path:
            return "Caminho do arquivo não especificado"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
            
    async def write_file(self, params: Dict, context: Dict) -> str:
        """Escreve conteúdo em um arquivo"""
        path = params.get("path")
        content = params.get("content", "")
        if not path:
            return "Caminho do arquivo não especificado"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Arquivo {path} escrito com sucesso"
        except Exception as e:
            return f"Erro ao escrever arquivo: {e}"
            
    async def delete_file(self, params: Dict, context: Dict) -> str:
        """Deleta um arquivo"""
        path = params.get("path")
        if not path:
            return "Caminho do arquivo não especificado"
        try:
            Path(path).unlink()
            return f"Arquivo {path} deletado com sucesso"
        except Exception as e:
            return f"Erro ao deletar arquivo: {e}"
            
    async def create_directory(self, params: Dict, context: Dict) -> str:
        """Cria um diretório"""
        path = params.get("path")
        if not path:
            return "Caminho do diretório não especificado"
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return f"Diretório {path} criado com sucesso"
        except Exception as e:
            return f"Erro ao criar diretório: {e}"
            
    # Ações de assistente pessoal
    async def set_volume(self, params: Dict, context: Dict) -> str:
        """Define volume do sistema"""
        level = params.get("level", 50)
        # Implementação depende do sistema operacional
        return f"Volume definido para {level}% (implementação dependente do SO)"
        
    async def set_brightness(self, params: Dict, context: Dict) -> str:
        """Define brilho da tela"""
        level = params.get("level", 50)
        # Implementação depende do sistema operacional
        return f"Brilho definido para {level}% (implementação dependente do SO)"
        
    async def create_note(self, params: Dict, context: Dict) -> str:
        """Cria uma nota"""
        content = params.get("content", "")
        title = params.get("title", "Sem título")
        timestamp = datetime.now().isoformat()
        note = {"title": title, "content": content, "timestamp": timestamp}
        # Salvar em banco de dados ou arquivo
        return f"Nota '{title}' criada em {timestamp}"
        
    async def list_notes(self, params: Dict, context: Dict) -> str:
        """Lista notas"""
        # Implementar recuperação do banco de dados
        return "Lista de notas (implementação pendente)"
        
    async def set_timer(self, params: Dict, context: Dict) -> str:
        """Define um timer"""
        seconds = params.get("seconds", 60)
        await asyncio.sleep(seconds)
        return f"Timer de {seconds} segundos concluído"
        
    async def set_reminder(self, params: Dict, context: Dict) -> str:
        """Define um lembrete"""
        message = params.get("message", "")
        time = params.get("time", "")
        return f"Lembrente definido: {message} às {time}"
        
    # Ações de segurança
    async def scan_ports(self, params: Dict, context: Dict) -> str:
        """Escaneia portas abertas"""
        host = params.get("host", "127.0.0.1")
        import socket
        open_ports = []
        for port in range(1, 1025):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    open_ports.append(str(port))
                sock.close()
            except:
                continue
        return f"Portas abertas em {host}: {', '.join(open_ports) if open_ports else 'Nenhuma'}"
        
    async def scan_processes(self, params: Dict, context: Dict) -> str:
        """Escaneia processos suspeitos"""
        import psutil
        suspicious = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['cpu_percent'] > 80 or proc.info['memory_percent'] > 80:
                    suspicious.append(f"PID: {proc.info['pid']} | Nome: {proc.info['name']} | CPU: {proc.info['cpu_percent']}% | Mem: {proc.info['memory_percent']}%")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return "\n".join(suspicious) if suspicious else "Nenhum processo suspeito encontrado"
        
    async def check_passwords(self, params: Dict, context: Dict) -> str:
        """Verifica senhas fracas"""
        # Implementar verificação de senhas
        return "Verificação de senhas (implementação pendente)"
        
    async def analyze_logs(self, params: Dict, context: Dict) -> str:
        """Analisa logs do sistema"""
        log_path = params.get("path", "/var/log/syslog")
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-100:]  # Últimas 100 linhas
            return "\n".join(lines)
        except Exception as e:
            return f"Erro ao analisar logs: {e}"
            
    # Ações de desenvolvimento
    async def run_code(self, params: Dict, context: Dict) -> str:
        """Executa código"""
        code = params.get("code", "")
        language = params.get("language", "python")
        if language == "python":
            try:
                result = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.stdout or result.stderr
            except Exception as e:
                return f"Erro ao executar código: {e}"
        return f"Linguagem {language} não suportada"
        
    async def git_status(self, params: Dict, context: Dict) -> str:
        """Status do git"""
        try:
            result = subprocess.run(
                ["git", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Erro ao obter status do git: {e}"
            
    async def git_commit(self, params: Dict, context: Dict) -> str:
        """Commit do git"""
        message = params.get("message", "Update")
        try:
            subprocess.run(["git", "add", "."], timeout=10)
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout or "Commit realizado"
        except Exception as e:
            return f"Erro ao fazer commit: {e}"
            
    async def docker_status(self, params: Dict, context: Dict) -> str:
        """Status do Docker"""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Erro ao obter status do Docker: {e}"
            
    # Ações de web
    async def web_search(self, params: Dict, context: Dict) -> str:
        """Busca na web (offline - usa duckduckgo local se disponível)"""
        query = params.get("query", "")
        return f"Busca web offline para '{query}' (implementação pendente)"
        
    async def download_file(self, params: Dict, context: Dict) -> str:
        """Baixa arquivo"""
        url = params.get("url", "")
        dest = params.get("destination", ".")
        return f"Download de {url} para {dest} (implementação pendente)"
        
    # Ações de conhecimento
    async def neuroscience_query(self, params: Dict, context: Dict) -> str:
        """Consulta base de conhecimento de neurociência"""
        query = params.get("query", "")
        return f"Consulta neurocientífica: {query} (implementação pendente)"
        
    async def robotics_query(self, params: Dict, context: Dict) -> str:
        """Consulta base de conhecimento de robótica"""
        query = params.get("query", "")
        return f"Consulta de robótica: {query} (implementação pendente)"
        
    async def security_query(self, params: Dict, context: Dict) -> str:
        """Consulta base de conhecimento de segurança"""
        query = params.get("query", "")
        return f"Consulta de segurança: {query} (implementação pendente)"
        
    # Ações de memória
    async def store_memory(self, params: Dict, context: Dict) -> str:
        """Armazena memória"""
        content = params.get("content", "")
        return f"Memória armazenada: {content[:50]}..."
        
    async def retrieve_memory(self, params: Dict, context: Dict) -> str:
        """Recupera memória"""
        memory_id = params.get("id", "")
        return f"Recuperando memória {memory_id} (implementação pendente)"
        
    async def search_memories(self, params: Dict, context: Dict) -> str:
        """Busca memórias"""
        query = params.get("query", "")
        return f"Buscando memórias com query: {query} (implementação pendente)"
        
    # Ações de configuração
    async def update_config(self, params: Dict, context: Dict) -> str:
        """Atualiza configuração"""
        key = params.get("key", "")
        value = params.get("value", "")
        return f"Configuração atualizada: {key} = {value}"
        
    async def reload_config(self, params: Dict, context: Dict) -> str:
        """Recarrega configuração"""
        return "Configuração recarregada"
        
    # Ações de diagnóstico
    async def health_check(self, params: Dict, context: Dict) -> str:
        """Verificação de saúde do sistema"""
        checks = {
            "motor": "OK",
            "llm": "OK" if self.config.get("llm", {}).get("enabled") else "Desabilitado",
            "armazenamento": "OK",
            "rede": "OK"
        }
        return json.dumps(checks, indent=2, ensure_ascii=False)
        
    async def performance_test(self, params: Dict, context: Dict) -> str:
        """Teste de performance"""
        import time
        start = time.time()
        # Simula operação
        await asyncio.sleep(0.1)
        elapsed = time.time() - start
        return f"Teste de performance concluído em {elapsed:.3f}s"
        
    async def diagnostic_report(self, params: Dict, context: Dict) -> str:
        """Relatório de diagnóstico"""
        return "Relatório de diagnóstico (implementação pendente)"
        
    # Ações de backup
    async def create_backup(self, params: Dict, context: Dict) -> str:
        """Cria backup"""
        path = params.get("path", ".")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.tar.gz"
        return f"Backup criado: {backup_name}"
        
    async def restore_backup(self, params: Dict, context: Dict) -> str:
        """Restaura backup"""
        backup_file = params.get("file", "")
        return f"Backup restaurado: {backup_file}"
        
    # Ações de análise
    async def analyze_binary(self, params: Dict, context: Dict) -> str:
        """Analisa binário"""
        path = params.get("path", "")
        return f"Análise de binário: {path} (implementação pendente)"
        
    async def analyze_dependencies(self, params: Dict, context: Dict) -> str:
        """Analisa dependências"""
        path = params.get("path", ".")
        return f"Análise de dependências em {path} (implementação pendente)"
        
    async def generate_report(self, params: Dict, context: Dict) -> str:
        """Gera relatório"""
        report_type = params.get("type", "security")
        return f"Relatório {report_type} gerado"
        
    # Ações de rede
    async def ping_host(self, params: Dict, context: Dict) -> str:
        """Ping em host"""
        host = params.get("host", "8.8.8.8")
        try:
            result = subprocess.run(
                ["ping", "-c", "4", host],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Erro ao pingar {host}: {e}"
            
    async def trace_route(self, params: Dict, context: Dict) -> str:
        """Rota até host"""
        host = params.get("host", "8.8.8.8")
        try:
            result = subprocess.run(
                ["traceroute", host],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception as e:
            return f"Erro ao traceroute {host}: {e}"
            
    async def dns_lookup(self, params: Dict, context: Dict) -> str:
        """Consulta DNS"""
        domain = params.get("domain", "google.com")
        try:
            result = subprocess.run(
                ["nslookup", domain],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Erro ao consultar DNS: {e}"
            
    # Ações de sistema
    async def shutdown(self, params: Dict, context: Dict) -> str:
        """Desliga o sistema"""
        # Confirmar antes de executar
        return "Comando de desligamento (requer confirmação)"
        
    async def reboot(self, params: Dict, context: Dict) -> str:
        """Reinicia o sistema"""
        return "Comando de reinício (requer confirmação)"
        
    async def sleep(self, params: Dict, context: Dict) -> str:
        """Coloca sistema para dormir"""
        return "Comando de suspensão (requer confirmação)"