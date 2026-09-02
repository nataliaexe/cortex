#!/usr/bin/env python3
"""
Gênesis Córtex - Process Analyzer
Análise avançada de processos
"""

import logging
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime


class ProcessAnalyzer:
    """Analisador de processos do sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
    def analyze_all_processes(self) -> Dict[str, Any]:
        """Analisa todos os processos em execução"""
        processes = []
        suspicious = []
        high_resource = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
            try:
                process_info = {
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent'],
                    'cmdline': proc.info['cmdline'],
                    'create_time': datetime.fromtimestamp(proc.info['create_time']).isoformat() if proc.info['create_time'] else None
                }
                
                processes.append(process_info)
                
                # Classifica como suspeito
                if self._is_suspicious(process_info):
                    suspicious.append(process_info)
                    
                # Classifica como alto consumo de recursos
                if self._is_high_resource(process_info):
                    high_resource.append(process_info)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return {
            'total_processes': len(processes),
            'suspicious_count': len(suspicious),
            'high_resource_count': len(high_resource),
            'suspicious': suspicious,
            'high_resource': high_resource,
            'all_processes': processes
        }
        
    def _is_suspicious(self, process: Dict[str, Any]) -> bool:
        """Verifica se processo é suspeito"""
        suspicious_names = [
            'powershell.exe', 'cmd.exe', 'bash', 'sh',
            'netcat', 'nc', 'telnet', 'ssh',
            'python', 'perl', 'ruby'
        ]
        
        # Nome genérico ou suspeito
        if process['name'] in suspicious_names:
            return True
            
        # Sem cmdline (oculto)
        if not process['cmdline']:
            return True
            
        # Cmdline suspeito
        cmdline_str = ' '.join(process['cmdline']).lower()
        suspicious_keywords = [
            'reverse', 'shell', 'bind', 'backdoor',
            'keylogger', 'password', 'steal',
            'crypt', 'miner', 'bitcoin'
        ]
        
        for keyword in suspicious_keywords:
            if keyword in cmdline_str:
                return True
                
        return False
        
    def _is_high_resource(self, process: Dict[str, Any]) -> bool:
        """Verifica se processo consome muitos recursos"""
        cpu_threshold = 80.0
        memory_threshold = 80.0
        
        return (process['cpu_percent'] > cpu_threshold or 
                process['memory_percent'] > memory_threshold)
                
    def get_process_details(self, pid: int) -> Dict[str, Any]:
        """Obtém detalhes específicos de um processo"""
        try:
            proc = psutil.Process(pid)
            
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'username': proc.username(),
                'status': proc.status(),
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.memory_percent(),
                'memory_info': {
                    'rss': proc.memory_info().rss,
                    'vms': proc.memory_info().vms
                },
                'num_threads': proc.num_threads(),
                'cmdline': proc.cmdline(),
                'create_time': datetime.fromtimestamp(proc.create_time()).isoformat(),
                'connections': len(proc.connections()),
                'open_files': len(proc.open_files()) if hasattr(proc, 'open_files') else 0,
                'children': [child.pid for child in proc.children()]
            }
            
        except psutil.NoSuchProcess:
            return {'error': f'Processo {pid} não encontrado'}
        except psutil.AccessDenied:
            return {'error': f'Acesso negado ao processo {pid}'}
            
    def kill_process(self, pid: int) -> bool:
        """Termina um processo"""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except psutil.NoSuchProcess:
            self.logger.error(f'Processo {pid} não encontrado')
            return False
        except psutil.AccessDenied:
            self.logger.error(f'Acesso negado ao processo {pid}')
            return False
            
    def get_network_connections(self) -> List[Dict[str, Any]]:
        """Obtém conexões de rede dos processos"""
        connections = []
        
        for conn in psutil.net_connections():
            try:
                connections.append({
                    'local_address': conn.laddr,
                    'remote_address': conn.raddr,
                    'status': conn.status,
                    'pid': conn.pid,
                    'protocol': conn.type
                })
            except Exception:
                continue
                
        return connections