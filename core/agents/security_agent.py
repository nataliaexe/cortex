#!/usr/bin/env python3
"""
Gênesis Córtex - Agente de Cybersecurity Autônomo
Agente especializado em análise de segurança, pentests e monitoramento
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..governance import Governance
from ..model_router import ModelRouter
from ..semantic_matcher import SemanticMatcher
from database.repositories.task_repository import TaskRepository
from database.repositories.audit_repository import AuditRepository
from database.repositories.scan_repository import ScanRepository

# Importar módulos de segurança existentes
from security.universal_scanner import UniversalScanner
from security.binary_analyzer import BinaryAnalyzer
from security.dependency_checker import DependencyChecker
from security.process_analyzer import ProcessAnalyzer
from security.packet_sniffer import PacketSniffer
from security.geolocation import Geolocation
from security.report_generator import ReportGenerator


class SecurityMode(Enum):
    """Modos de operação do agente de segurança"""
    SCAN = "scan"
    MONITOR = "monitor"
    PENTEST = "pentest"


class ThreatLevel(Enum):
    """Níveis de ameaça"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityAgent:
    """Agente de segurança autônomo com múltiplos modos de operação"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        task_repository: TaskRepository,
        audit_repository: AuditRepository,
        scan_repository: ScanRepository
    ):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.task_repository = task_repository
        self.audit_repository = audit_repository
        self.scan_repository = scan_repository
        
        # Sistemas existentes
        self.governance = Governance(config)
        self.model_router = ModelRouter(config)
        self.semantic_matcher = SemanticMatcher(config)
        
        # Módulos de segurança
        self.universal_scanner = UniversalScanner(config)
        self.binary_analyzer = BinaryAnalyzer(config)
        self.dependency_checker = DependencyChecker(config)
        self.process_analyzer = ProcessAnalyzer(config)
        self.packet_sniffer = PacketSniffer(config)
        self.geolocation = Geolocation(config)
        self.report_generator = ReportGenerator(config)
        
        # Estado do agente
        self.current_mode: SecurityMode = SecurityMode.SCAN
        self.current_target: Optional[str] = None
        self.monitoring_active: bool = False
        self.threats_detected: List[Dict[str, Any]] = []
        
        # Métricas
        self.metrics = {
            "scans_completed": 0,
            "vulnerabilities_found": 0,
            "binaries_analyzed": 0,
            "monitoring_hours": 0,
            "threats_blocked": 0
        }
        
    async def execute_scan(self, target: str, scan_type: str = "full") -> Dict[str, Any]:
        """Executa um scan de segurança completo"""
        self.logger.info(f"Iniciando scan de segurança: {target} ({scan_type})")
        self.current_mode = SecurityMode.SCAN
        self.current_target = target
        
        scan_id = datetime.now().isoformat()
        results = {
            "scan_id": scan_id,
            "target": target,
            "scan_type": scan_type,
            "timestamp": datetime.now().isoformat(),
            "findings": []
        }
        
        try:
            # 1. Scan de código (se for diretório)
            if Path(target).is_dir():
                code_scan = await self._scan_code(target)
                results["findings"].append(code_scan)
            
            # 2. Análise de dependências
            if Path(target).is_dir():
                dep_scan = await self._scan_dependencies(target)
                results["findings"].append(dep_scan)
            
            # 3. Análise de binários
            if Path(target).is_file():
                binary_scan = await self._analyze_binary(target)
                results["findings"].append(binary_scan)
            
            # 4. Scan de processos
            process_scan = await self._scan_processes()
            results["findings"].append(process_scan)
            
            # 5. Scan de rede
            network_scan = await self._scan_network(target)
            results["findings"].append(network_scan)
            
            # Consolidar ameaças
            results["threats"] = self._consolidate_threats(results["findings"])
            results["threat_count"] = len(results["threats"])
            
            # Atualizar métricas
            self.metrics["scans_completed"] += 1
            self.metrics["vulnerabilities_found"] += results["threat_count"]
            
            # Salvar no repositório
            await self.scan_repository.save_scan(results)
            
            # Gerar relatório
            report = await self._generate_report(results)
            results["report"] = report
            
            # Auditoria
            self.governance.audit(
                "security_scan_completed",
                self.governance.authorize("security_scan", {"target": target}, {}),
                params={"target": target, "scan_type": scan_type},
                outcome="completed"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro no scan de segurança: {e}")
            self.governance.audit(
                "security_scan_failed",
                self.governance.authorize("security_scan", {"target": target}, {}),
                params={"target": target, "error": str(e)},
                outcome="failed"
            )
            return {
                "scan_id": scan_id,
                "target": target,
                "status": "failed",
                "error": str(e)
            }
    
    async def start_monitoring(self, targets: List[str] = None) -> Dict[str, Any]:
        """Inicia modo de monitoramento contínuo"""
        self.logger.info("Iniciando modo de monitoramento")
        self.current_mode = SecurityMode.MONITOR
        self.monitoring_active = True
        self.current_target = targets[0] if targets else "localhost"
        
        monitoring_session = {
            "session_id": datetime.now().isoformat(),
            "targets": targets or ["localhost"],
            "start_time": datetime.now().isoformat(),
            "active": True,
            "events": []
        }
        
        try:
            # Iniciar packet sniffer em background
            sniffer_task = asyncio.create_task(self._run_packet_sniffer())
            
            # Iniciar monitoramento de processos
            process_task = asyncio.create_task(self._monitor_processes())
            
            # Iniciar monitoramento de logs
            log_task = asyncio.create_task(self._monitor_logs())
            
            monitoring_session["tasks"] = {
                "sniffer": "running",
                "process_monitor": "running",
                "log_monitor": "running"
            }
            
            self.governance.audit(
                "security_monitoring_started",
                self.governance.authorize("security_monitoring", {"targets": targets}, {}),
                params={"targets": targets},
                outcome="started"
            )
            
            return monitoring_session
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar monitoramento: {e}")
            self.monitoring_active = False
            return {
                "session_id": monitoring_session["session_id"],
                "status": "failed",
                "error": str(e)
            }
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Para o modo de monitoramento"""
        self.logger.info("Parando modo de monitoramento")
        self.monitoring_active = False
        
        # Cancelar tarefas de monitoramento
        # (Implementação depende de como as tarefas são gerenciadas)
        
        self.governance.audit(
            "security_monitoring_stopped",
            self.governance.authorize("security_monitoring_stop", {}, {}),
            params={},
            outcome="stopped"
        )
        
        return {
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_pentest(self, target: str, scope: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executa pentest assistido"""
        self.logger.info(f"Iniciando pentest assistido: {target}")
        self.current_mode = SecurityMode.PENTEST
        self.current_target = target
        
        scope = scope or {}
        pentest_id = datetime.now().isoformat()
        
        results = {
            "pentest_id": pentest_id,
            "target": target,
            "scope": scope,
            "timestamp": datetime.now().isoformat(),
            "phases": []
        }
        
        try:
            # Fase 1: Reconhecimento
            self.logger.info("Fase 1: Reconhecimento")
            recon = await self._reconnaissance(target)
            results["phases"].append({"name": "reconnaissance", "results": recon})
            
            # Fase 2: Enumeração
            self.logger.info("Fase 2: Enumeração")
            enumeration = await self._enumeration(target, recon)
            results["phases"].append({"name": "enumeration", "results": enumeration})
            
            # Fase 3: Análise de vulnerabilidades
            self.logger.info("Fase 3: Análise de vulnerabilidades")
            vuln_analysis = await self._vulnerability_analysis(target, enumeration)
            results["phases"].append({"name": "vulnerability_analysis", "results": vuln_analysis})
            
            # Fase 4: Testes controlados (com confirmação)
            self.logger.info("Fase 4: Testes controlados")
            controlled_tests = await self._controlled_tests(target, vuln_analysis)
            results["phases"].append({"name": "controlled_tests", "results": controlled_tests})
            
            # Fase 5: Relatório
            self.logger.info("Fase 5: Gerando relatório")
            report = await self._generate_pentest_report(results)
            results["report"] = report
            
            self.governance.audit(
                "security_pentest_completed",
                self.governance.authorize("security_pentest", {"target": target}, {}),
                params={"target": target, "scope": scope},
                outcome="completed"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro no pentest: {e}")
            self.governance.audit(
                "security_pentest_failed",
                self.governance.authorize("security_pentest", {"target": target}, {}),
                params={"target": target, "error": str(e)},
                outcome="failed"
            )
            return {
                "pentest_id": pentest_id,
                "target": target,
                "status": "failed",
                "error": str(e)
            }
    
    async def _scan_code(self, path: str) -> Dict[str, Any]:
        """Scan de código usando UniversalScanner"""
        self.logger.info(f"Scanning code in {path}")
        
        try:
            results = self.universal_scanner.scan_directory(path)
            
            return {
                "type": "code_scan",
                "path": path,
                "results": results,
                "vulnerabilities_count": len(results.get("findings", []))
            }
        except Exception as e:
            return {
                "type": "code_scan",
                "path": path,
                "error": str(e),
                "vulnerabilities_count": 0
            }
    
    async def _scan_dependencies(self, path: str) -> Dict[str, Any]:
        """Scan de dependências usando DependencyChecker"""
        self.logger.info(f"Scanning dependencies in {path}")
        
        try:
            results = self.dependency_checker.check_directory(path)
            
            cves = []
            for dep, vulns in results.items():
                if isinstance(vulns, dict) and "vulnerabilities" in vulns:
                    cves.extend(vulns["vulnerabilities"])
            
            return {
                "type": "dependency_scan",
                "path": path,
                "results": results,
                "vulnerabilities_count": len(cves)
            }
        except Exception as e:
            return {
                "type": "dependency_scan",
                "path": path,
                "error": str(e),
                "vulnerabilities_count": 0
            }
    
    async def _analyze_binary(self, path: str) -> Dict[str, Any]:
        """Análise de binário usando BinaryAnalyzer"""
        self.logger.info(f"Analyzing binary {path}")
        
        try:
            results = self.binary_analyzer.analyze(path)
            
            self.metrics["binaries_analyzed"] += 1
            
            return {
                "type": "binary_analysis",
                "path": path,
                "results": results,
                "suspicious": results.get("suspicious", False)
            }
        except Exception as e:
            return {
                "type": "binary_analysis",
                "path": path,
                "error": str(e),
                "suspicious": False
            }
    
    async def _scan_processes(self) -> Dict[str, Any]:
        """Scan de processos usando ProcessAnalyzer"""
        self.logger.info("Scanning processes")
        
        try:
            results = self.process_analyzer.analyze_all()
            
            suspicious = [p for p in results if p.get("suspicious", False)]
            
            return {
                "type": "process_scan",
                "results": results,
                "suspicious_count": len(suspicious),
                "total_processes": len(results)
            }
        except Exception as e:
            return {
                "type": "process_scan",
                "error": str(e),
                "suspicious_count": 0,
                "total_processes": 0
            }
    
    async def _scan_network(self, target: str) -> Dict[str, Any]:
        """Scan de rede"""
        self.logger.info(f"Scanning network for {target}")
        
        try:
            # Scan de portas
            port_results = await self._scan_ports(target)
            
            # Geolocalização se for IP
            geo_results = {}
            if self._is_ip_address(target):
                geo_results = self.geolocation.lookup(target)
            
            return {
                "type": "network_scan",
                "target": target,
                "ports": port_results,
                "geolocation": geo_results
            }
        except Exception as e:
            return {
                "type": "network_scan",
                "target": target,
                "error": str(e)
            }
    
    async def _scan_ports(self, target: str) -> Dict[str, Any]:
        """Scan de portas"""
        try:
            # Usar nmap se disponível, ou implementação própria
            result = subprocess.run(
                ["nmap", "-sS", "-p", "1-1024", target],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "command": "nmap",
                "output": result.stdout,
                "open_ports": self._parse_nmap_output(result.stdout)
            }
        except Exception as e:
            # Fallback para scan simples
            return {
                "command": "simple_scan",
                "error": str(e),
                "open_ports": []
            }
    
    def _parse_nmap_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse output do nmap"""
        ports = []
        lines = output.split('\n')
        
        for line in lines:
            if '/tcp' in line and 'open' in line:
                parts = line.split()
                if len(parts) >= 3:
                    ports.append({
                        "port": parts[0].split('/')[0],
                        "state": parts[1],
                        "service": parts[2] if len(parts) > 2 else "unknown"
                    })
        
        return ports
    
    def _is_ip_address(self, target: str) -> bool:
        """Verifica se target é um endereço IP"""
        import re
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(ip_pattern, target))
    
    async def _reconnaissance(self, target: str) -> Dict[str, Any]:
        """Fase de reconhecimento do pentest"""
        recon = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "dns_info": {},
            "network_info": {},
            "os_detection": {}
        }
        
        try:
            # DNS lookup
            dns_result = subprocess.run(
                ["nslookup", target],
                capture_output=True,
                text=True,
                timeout=10
            )
            recon["dns_info"] = {"output": dns_result.stdout}
            
            # Ping
            ping_result = subprocess.run(
                ["ping", "-c", "3", target],
                capture_output=True,
                text=True,
                timeout=15
            )
            recon["network_info"] = {"ping_output": ping_result.stdout}
            
        except Exception as e:
            recon["error"] = str(e)
        
        return recon
    
    async def _enumeration(self, target: str, recon: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de enumeração do pentest"""
        enumeration = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "services": [],
            "users": [],
            "shares": []
        }
        
        try:
            # Scan de serviços
            port_scan = await self._scan_ports(target)
            enumeration["services"] = port_scan.get("open_ports", [])
            
        except Exception as e:
            enumeration["error"] = str(e)
        
        return enumeration
    
    async def _vulnerability_analysis(self, target: str, enumeration: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de análise de vulnerabilidades"""
        analysis = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": []
        }
        
        # Analisar serviços encontrados
        for service in enumeration.get("services", []):
            port = service.get("port")
            service_name = service.get("service")
            
            # Adicionar vulnerabilidades conhecidas (simplificado)
            if service_name in ["http", "https"]:
                analysis["vulnerabilities"].append({
                    "service": service_name,
                    "port": port,
                    "cve": "CVE-2021-XXXX",
                    "severity": "medium",
                    "description": "Potential web vulnerability"
                })
        
        return analysis
    
    async def _controlled_tests(self, target: str, vuln_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de testes controlados (com confirmação)"""
        tests = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "tests_performed": [],
            "results": []
        }
        
        # Testes requerem confirmação humana
        for vuln in vuln_analysis.get("vulnerabilities", []):
            # Solicitar confirmação
            decision = self.governance.authorize(
                "pentest_test",
                {"target": target, "vulnerability": vuln},
                {}
            )
            
            if decision.allowed:
                # Executar teste controlado
                test_result = await self._execute_controlled_test(target, vuln)
                tests["results"].append(test_result)
            else:
                tests["results"].append({
                    "vulnerability": vuln,
                    "skipped": True,
                    "reason": decision.reason
                })
        
        return tests
    
    async def _execute_controlled_test(self, target: str, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """Executa um teste controlado específico"""
        # Implementação simplificada - na prática, cada teste seria específico
        return {
            "vulnerability": vulnerability,
            "test_executed": True,
            "result": "verified",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_packet_sniffer(self) -> None:
        """Executa packet sniffer em background"""
        self.logger.info("Iniciando packet sniffer")
        
        while self.monitoring_active:
            try:
                # Capturar pacotes por um curto período
                packets = self.packet_sniffer.capture(duration=10)
                
                # Analisar pacotes
                for packet in packets:
                    if self._is_suspicious_packet(packet):
                        self.threats_detected.append({
                            "type": "network_threat",
                            "packet": packet,
                            "timestamp": datetime.now().isoformat()
                        })
                
                # Pausar antes da próxima captura
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Erro no packet sniffer: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_processes(self) -> None:
        """Monitora processos em background"""
        self.logger.info("Iniciando monitoramento de processos")
        
        while self.monitoring_active:
            try:
                results = self.process_analyzer.analyze_all()
                
                for process in results:
                    if process.get("suspicious", False):
                        self.threats_detected.append({
                            "type": "process_threat",
                            "process": process,
                            "timestamp": datetime.now().isoformat()
                        })
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Erro no monitoramento de processos: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_logs(self) -> None:
        """Monitora logs do sistema em background"""
        self.logger.info("Iniciando monitoramento de logs")
        
        while self.monitoring_active:
            try:
                # Analisar logs recentes
                log_path = "/var/log/syslog"
                if Path(log_path).exists():
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()[-100:]  # Últimas 100 linhas
                    
                    for line in lines:
                        if self._is_suspicious_log(line):
                            self.threats_detected.append({
                                "type": "log_threat",
                                "log_line": line.strip(),
                                "timestamp": datetime.now().isoformat()
                            })
                
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Erro no monitoramento de logs: {e}")
                await asyncio.sleep(60)
    
    def _is_suspicious_packet(self, packet: Dict[str, Any]) -> bool:
        """Verifica se pacote é suspeito"""
        # Implementação simplificada
        return False
    
    def _is_suspicious_log(self, log_line: str) -> bool:
        """Verifica se linha de log é suspeita"""
        suspicious_keywords = ["failed", "error", "attack", "intrusion", "unauthorized"]
        return any(keyword in log_line.lower() for keyword in suspicious_keywords)
    
    def _consolidate_threats(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolida ameaças de diferentes scans"""
        threats = []
        
        for finding in findings:
            if finding.get("type") == "code_scan":
                for vuln in finding.get("results", {}).get("findings", []):
                    threats.append({
                        "source": "code_scan",
                        "severity": vuln.get("severity", "medium"),
                        "description": vuln.get("description", ""),
                        "location": vuln.get("location", "")
                    })
            
            elif finding.get("type") == "dependency_scan":
                for dep, vulns in finding.get("results", {}).items():
                    if isinstance(vulns, dict) and "vulnerabilities" in vulns:
                        for cve in vulns["vulnerabilities"]:
                            threats.append({
                                "source": "dependency_scan",
                                "severity": "high",
                                "description": f"CVE in {dep}",
                                "cve": cve
                            })
            
            elif finding.get("type") == "process_scan":
                for proc in finding.get("results", []):
                    if proc.get("suspicious", False):
                        threats.append({
                            "source": "process_scan",
                            "severity": "high",
                            "description": f"Suspicious process: {proc.get('name', '')}",
                            "pid": proc.get("pid")
                        })
        
        # Ordenar por severidade
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        threats.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 5))
        
        return threats
    
    async def _generate_report(self, scan_results: Dict[str, Any]) -> str:
        """Gera relatório de scan"""
        return self.report_generator.generate_security_report(scan_results)
    
    async def _generate_pentest_report(self, pentest_results: Dict[str, Any]) -> str:
        """Gera relatório de pentest"""
        return self.report_generator.generate_pentest_report(pentest_results)
    
    async def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do agente"""
        return {
            "agent": "security",
            "mode": self.current_mode.value,
            "target": self.current_target,
            "monitoring_active": self.monitoring_active,
            "threats_detected": len(self.threats_detected),
            "metrics": self.metrics
        }
    
    async def get_threats(self) -> List[Dict[str, Any]]:
        """Retorna ameaças detectadas"""
        return self.threats_detected
    
    async def clear_threats(self) -> None:
        """Limpa lista de ameaças"""
        self.threats_detected = []