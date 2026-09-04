#!/usr/bin/env python3
"""
Gênesis Córtex - Agente de Auto-Evolução
Agente especializado em aprendizado contínuo e melhoria do sistema
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from ..governance import Governance
from ..model_router import ModelRouter
from ..semantic_matcher import SemanticMatcher
from ..self_modification.safe_editor import SafeEditor
from ..self_modification.capability_discovery import CapabilityDiscovery
from ..self_modification.sandbox_tester import SandboxTester
from ..self_modification.continuous_evolution import ContinuousEvolution
from database.repositories.task_repository import TaskRepository
from database.repositories.audit_repository import AuditRepository


class LearningPhase(Enum):
    """Fases do ciclo de aprendizado"""
    ANALYSIS = "analysis"
    DISCOVERY = "discovery"
    PROPOSAL = "proposal"
    TESTING = "testing"
    APPLICATION = "application"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"


class EvolutionAgent:
    """Agente de auto-evolução com sistema de aprendizado contínuo"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        task_repository: TaskRepository,
        audit_repository: AuditRepository
    ):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.task_repository = task_repository
        self.audit_repository = audit_repository
        
        # Sistemas existentes
        self.governance = Governance(config)
        self.model_router = ModelRouter(config)
        self.semantic_matcher = SemanticMatcher(config)
        self.safe_editor = SafeEditor(config)
        self.capability_discovery = CapabilityDiscovery(config)
        self.sandbox_tester = SandboxTester(config)
        self.continuous_evolution = ContinuousEvolution(config)
        
        # Estado do agente
        self.learning_enabled: bool = config.get("self_modification", {}).get("enabled", False)
        self.current_phase: LearningPhase = LearningPhase.ANALYSIS
        self.memory_embeddings: List[Dict[str, Any]] = []
        self.learning_history: List[Dict[str, Any]] = []
        
        # Métricas de aprendizado
        self.metrics = {
            "improvements_proposed": 0,
            "improvements_applied": 0,
            "patterns_discovered": 0,
            "bugs_fixed": 0,
            "performance_gains": 0.0,
            "learning_cycles": 0
        }
        
        # Memória de longo prazo (simulada - na prática usaria LanceDB)
        self.long_term_memory: Dict[str, Any] = {
            "successful_solutions": [],
            "common_errors": [],
            "performance_patterns": [],
            "user_feedback": []
        }
        
    async def enable_learning(self) -> Dict[str, Any]:
        """Habilita o modo de aprendizado"""
        self.logger.info("Habilitando modo de aprendizado")
        self.learning_enabled = True
        
        self.governance.audit(
            "evolution_learning_enabled",
            self.governance.authorize("enable_learning", {}, {}),
            params={},
            outcome="enabled"
        )
        
        return {
            "status": "enabled",
            "timestamp": datetime.now().isoformat()
        }
    
    async def disable_learning(self) -> Dict[str, Any]:
        """Desabilita o modo de aprendizado"""
        self.logger.info("Desabilitando modo de aprendizado")
        self.learning_enabled = False
        
        self.governance.audit(
            "evolution_learning_disabled",
            self.governance.authorize("disable_learning", {}, {}),
            params={},
            outcome="disabled"
        )
        
        return {
            "status": "disabled",
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_learning_cycle(self) -> Dict[str, Any]:
        """Executa um ciclo completo de aprendizado"""
        if not self.learning_enabled:
            return {"status": "disabled", "message": "Learning is disabled"}
        
        self.logger.info("Iniciando ciclo de aprendizado")
        cycle_id = datetime.now().isoformat()
        
        try:
            # Fase 1: Análise de logs e execuções
            self.current_phase = LearningPhase.ANALYSIS
            analysis = await self._analyze_execution_logs()
            
            # Fase 2: Descoberta de lacunas
            self.current_phase = LearningPhase.DISCOVERY
            gaps = await self._discover_capability_gaps()
            
            # Fase 3: Proposta de melhorias
            self.current_phase = LearningPhase.PROPOSAL
            proposals = await self._propose_improvements(analysis, gaps)
            
            # Fase 4: Testes em sandbox
            self.current_phase = LearningPhase.TESTING
            test_results = []
            for proposal in proposals:
                test_result = await self._test_in_sandbox(proposal)
                test_results.append(test_result)
            
            # Fase 5: Aplicação de melhorias validadas
            self.current_phase = LearningPhase.APPLICATION
            applied = []
            for proposal, test_result in zip(proposals, test_results):
                if test_result.get("success"):
                    application_result = await self._apply_improvement(proposal)
                    applied.append(application_result)
            
            # Fase 6: Validação
            self.current_phase = LearningPhase.VALIDATION
            validation = await self._validate_improvements(applied)
            
            # Fase 7: Documentação
            self.current_phase = LearningPhase.DOCUMENTATION
            await self._document_learning(cycle_id, analysis, gaps, proposals, test_results, applied, validation)
            
            # Atualizar métricas
            self.metrics["learning_cycles"] += 1
            self.metrics["improvements_proposed"] += len(proposals)
            self.metrics["improvements_applied"] += len(applied)
            
            # Adicionar ao histórico
            self.learning_history.append({
                "cycle_id": cycle_id,
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "gaps": gaps,
                "proposals": proposals,
                "test_results": test_results,
                "applied": applied,
                "validation": validation
            })
            
            self.governance.audit(
                "evolution_learning_cycle_completed",
                self.governance.authorize("learning_cycle", {}, {}),
                params={"cycle_id": cycle_id},
                outcome="completed"
            )
            
            return {
                "cycle_id": cycle_id,
                "status": "completed",
                "analysis": analysis,
                "gaps_discovered": len(gaps),
                "proposals": len(proposals),
                "applied": len(applied),
                "validation": validation,
                "metrics": self.metrics
            }
            
        except Exception as e:
            self.logger.error(f"Erro no ciclo de aprendizado: {e}")
            self.governance.audit(
                "evolution_learning_cycle_failed",
                self.governance.authorize("learning_cycle", {}, {}),
                params={"error": str(e)},
                outcome="failed"
            )
            return {
                "cycle_id": cycle_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _analyze_execution_logs(self) -> Dict[str, Any]:
        """Analisa logs de execuções para identificar padrões"""
        self.logger.info("Analisando logs de execução")
        
        analysis = {
            "error_patterns": [],
            "performance_issues": [],
            "user_satisfaction": [],
            "resource_usage": []
        }
        
        try:
            # Analisar logs do sistema
            log_path = Path("logs/cortex.log")
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    logs = f.readlines()[-1000:]  # Últimas 1000 linhas
                
                # Identificar padrões de erro
                error_patterns = self._identify_error_patterns(logs)
                analysis["error_patterns"] = error_patterns
                
                # Identificar problemas de performance
                performance_issues = self._identify_performance_issues(logs)
                analysis["performance_issues"] = performance_issues
            
            # Analisar histórico de tarefas
            task_history = await self.task_repository.get_recent_tasks(limit=100)
            if task_history:
                # Analisar taxa de sucesso
                success_rate = self._calculate_success_rate(task_history)
                analysis["success_rate"] = success_rate
                
                # Identificar tarefas mais frequentes
                frequent_tasks = self._identify_frequent_tasks(task_history)
                analysis["frequent_tasks"] = frequent_tasks
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de logs: {e}")
            analysis["error"] = str(e)
            return analysis
    
    def _identify_error_patterns(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Identifica padrões de erro nos logs"""
        patterns = []
        error_keywords = ["error", "exception", "failed", "timeout", "connection"]
        
        for log in logs:
            for keyword in error_keywords:
                if keyword in log.lower():
                    patterns.append({
                        "keyword": keyword,
                        "log": log.strip(),
                        "timestamp": self._extract_timestamp(log)
                    })
        
        # Consolidar padrões similares
        consolidated = self._consolidate_patterns(patterns)
        return consolidated
    
    def _identify_performance_issues(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Identifica problemas de performance nos logs"""
        issues = []
        performance_keywords = ["slow", "timeout", "latency", "memory", "cpu"]
        
        for log in logs:
            for keyword in performance_keywords:
                if keyword in log.lower():
                    issues.append({
                        "keyword": keyword,
                        "log": log.strip(),
                        "timestamp": self._extract_timestamp(log)
                    })
        
        return issues
    
    def _calculate_success_rate(self, tasks: List[Dict[str, Any]]) -> float:
        """Calcula taxa de sucesso das tarefas"""
        if not tasks:
            return 0.0
        
        successful = sum(1 for task in tasks if task.get("status") == "completed")
        return successful / len(tasks)
    
    def _identify_frequent_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifica tarefas mais frequentes"""
        task_counts = {}
        
        for task in tasks:
            task_type = task.get("type", "unknown")
            task_counts[task_type] = task_counts.get(task_type, 0) + 1
        
        # Ordenar por frequência
        sorted_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{"type": t, "count": c} for t, c in sorted_tasks[:10]]
    
    def _extract_timestamp(self, log: str) -> Optional[str]:
        """Extrai timestamp de um log"""
        # Implementação simplificada
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        match = re.search(timestamp_pattern, log)
        return match.group(0) if match else None
    
    def _consolidate_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolida padrões similares"""
        consolidated = {}
        
        for pattern in patterns:
            keyword = pattern["keyword"]
            if keyword not in consolidated:
                consolidated[keyword] = {
                    "keyword": keyword,
                    "count": 0,
                    "examples": []
                }
            consolidated[keyword]["count"] += 1
            if len(consolidated[keyword]["examples"]) < 3:
                consolidated[keyword]["examples"].append(pattern["log"])
        
        return list(consolidated.values())
    
    async def _discover_capability_gaps(self) -> List[Dict[str, Any]]:
        """Descobre lacunas entre PROJETO.md e implementação"""
        self.logger.info("Descobrindo lacunas de capacidades")
        
        try:
            # Usar CapabilityDiscovery existente
            gaps = self.capability_discovery.discover_gaps()
            
            self.metrics["patterns_discovered"] += len(gaps)
            
            return gaps
            
        except Exception as e:
            self.logger.error(f"Erro na descoberta de lacunas: {e}")
            return []
    
    async def _propose_improvements(self, analysis: Dict[str, Any], gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Propõe melhorias baseadas na análise e lacunas"""
        self.logger.info("Propondo melhorias")
        
        proposals = []
        
        # Propor melhorias para padrões de erro
        for error_pattern in analysis.get("error_patterns", []):
            if error_pattern.get("count", 0) > 5:  # Se ocorre mais de 5 vezes
                proposal = await self._propose_fix_for_error(error_pattern)
                if proposal:
                    proposals.append(proposal)
        
        # Propor melhorias para lacunas de capacidades
        for gap in gaps:
            proposal = await self._propose_implementation_for_gap(gap)
            if proposal:
                proposals.append(proposal)
        
        # Propor melhorias de performance
        for perf_issue in analysis.get("performance_issues", []):
            if perf_issue.get("count", 0) > 3:
                proposal = await self._propose_optimization(perf_issue)
                if proposal:
                    proposals.append(proposal)
        
        return proposals
    
    async def _propose_fix_for_error(self, error_pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Propõe fix para um padrão de erro"""
        prompt = f"""
Analise o seguinte padrão de erro e proponha uma solução:

Erro: {error_pattern.get('keyword')}
Ocorrências: {error_pattern.get('count')}
Exemplos: {error_pattern.get('examples', [])}

Forneça:
1. Causa provável
2. Solução proposta
3. Arquivos que precisam ser modificados
4. Código da solução
"""
        
        try:
            response = await self.model_router.route_request(
                prompt=prompt,
                task_type="reasoning"
            )
            
            return {
                "type": "error_fix",
                "error_pattern": error_pattern,
                "proposal": response,
                "priority": "high"
            }
        except Exception as e:
            self.logger.error(f"Erro ao propor fix: {e}")
            return None
    
    async def _propose_implementation_for_gap(self, gap: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Propõe implementação para uma lacuna"""
        prompt = f"""
Analise a seguinte lacuna de capacidade e proponha implementação:

Lacuna: {gap.get('description')}
Arquivo: {gap.get('file')}
Status: {gap.get('status')}

Forneça:
1. Plano de implementação
2. Arquivos a criar/modificar
3. Código necessário
4. Testes a implementar
"""
        
        try:
            response = await self.model_router.route_request(
                prompt=prompt,
                task_type="reasoning"
            )
            
            return {
                "type": "capability_implementation",
                "gap": gap,
                "proposal": response,
                "priority": "medium"
            }
        except Exception as e:
            self.logger.error(f"Erro ao propor implementação: {e}")
            return None
    
    async def _propose_optimization(self, perf_issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Propõe otimização para problema de performance"""
        prompt = f"""
Analise o seguinte problema de performance e proponha otimização:

Problema: {perf_issue.get('keyword')}
Ocorrências: {perf_issue.get('count')}
Exemplos: {perf_issue.get('examples', [])}

Forneça:
1. Causa provável
2. Otimização proposta
3. Impacto esperado
4. Código da otimização
"""
        
        try:
            response = await self.model_router.route_request(
                prompt=prompt,
                task_type="reasoning"
            )
            
            return {
                "type": "performance_optimization",
                "issue": perf_issue,
                "proposal": response,
                "priority": "medium"
            }
        except Exception as e:
            self.logger.error(f"Erro ao propor otimização: {e}")
            return None
    
    async def _test_in_sandbox(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Testa uma proposta em sandbox"""
        self.logger.info(f"Testando proposta em sandbox: {proposal.get('type')}")
        
        try:
            # Usar SandboxTester existente
            test_result = self.sandbox_tester.test_proposal(proposal)
            
            return {
                "proposal_type": proposal.get("type"),
                "success": test_result.get("success", False),
                "test_output": test_result.get("output", ""),
                "errors": test_result.get("errors", [])
            }
        except Exception as e:
            self.logger.error(f"Erro no teste sandbox: {e}")
            return {
                "proposal_type": proposal.get("type"),
                "success": False,
                "error": str(e)
            }
    
    async def _apply_improvement(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica uma melhoria validada"""
        self.logger.info(f"Aplicando melhoria: {proposal.get('type')}")
        
        try:
            # Extrair código da proposta
            code = self._extract_code_from_proposal(proposal)
            if not code:
                return {"success": False, "error": "No code found in proposal"}
            
            # Usar SafeEditor para aplicar mudanças
            result = self.safe_editor.apply_change(code)
            
            if result.get("success"):
                self.metrics["improvements_applied"] += 1
                
                # Adicionar à memória de longo prazo
                self._store_successful_solution(proposal, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao aplicar melhoria: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_code_from_proposal(self, proposal: Dict[str, Any]) -> Optional[str]:
        """Extrai código de uma proposta"""
        proposal_text = proposal.get("proposal", "")
        
        # Procurar por blocos de código
        import re
        code_patterns = [
            r'```python\n(.*?)```',
            r'```código\n(.*?)```',
            r'```\n(.*?)```'
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, proposal_text, re.DOTALL)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _store_successful_solution(self, proposal: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Armazena solução bem-sucedida na memória de longo prazo"""
        solution = {
            "type": proposal.get("type"),
            "problem": proposal.get("error_pattern") or proposal.get("gap") or proposal.get("issue"),
            "solution": proposal.get("proposal"),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.long_term_memory["successful_solutions"].append(solution)
        
        # Gerar embedding (simulado - na prática usaria Sentence-Transformers)
        embedding = self._generate_embedding(solution)
        self.memory_embeddings.append({
            "embedding": embedding,
            "solution": solution
        })
    
    def _generate_embedding(self, text: Dict[str, Any]) -> List[float]:
        """Gera embedding para texto (simulado)"""
        # Na prática, usaria sentence-transformers
        import hashlib
        text_str = json.dumps(text, sort_keys=True)
        hash_obj = hashlib.sha256(text_str.encode())
        
        # Converter hash em vetor de floats (simplificado)
        hash_int = int(hash_obj.hexdigest(), 16)
        return [(hash_int >> (i * 8)) & 0xFF / 255.0 for i in range(32)]
    
    async def _validate_improvements(self, applied: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valida as melhorias aplicadas"""
        self.logger.info("Validando melhorias aplicadas")
        
        validation = {
            "total_applied": len(applied),
            "successful": sum(1 for a in applied if a.get("success")),
            "failed": sum(1 for a in applied if not a.get("success")),
            "performance_impact": {}
        }
        
        # Executar testes de validação
        try:
            # Rodar testes existentes
            test_result = subprocess.run(
                ["pytest", "tests/", "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            validation["test_results"] = {
                "returncode": test_result.returncode,
                "output": test_result.stdout,
                "errors": test_result.stderr
            }
            
            # Medir impacto de performance
            before_metrics = self._get_performance_metrics()
            await asyncio.sleep(2)  # Pequena pausa
            after_metrics = self._get_performance_metrics()
            
            validation["performance_impact"] = {
                "before": before_metrics,
                "after": after_metrics,
                "change": self._calculate_performance_change(before_metrics, after_metrics)
            }
            
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def _get_performance_metrics(self) -> Dict[str, float]:
        """Obtém métricas de performance atuais"""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent
        }
    
    def _calculate_performance_change(self, before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
        """Calcula mudança de performance"""
        return {
            key: after[key] - before[key]
            for key in before.keys()
        }
    
    async def _document_learning(self, cycle_id: str, analysis: Dict[str, Any], gaps: List[Dict[str, Any]], 
                                proposals: List[Dict[str, Any]], test_results: List[Dict[str, Any]], 
                                applied: List[Dict[str, Any]], validation: Dict[str, Any]) -> None:
        """Documenta o ciclo de aprendizado"""
        self.logger.info("Documentando ciclo de aprendizado")
        
        doc = f"""
# Ciclo de Aprendizado: {cycle_id}

## Data: {datetime.now().isoformat()}

## Análise
{json.dumps(analysis, indent=2, ensure_ascii=False)}

## Lacunas Descobertas
{json.dumps(gaps, indent=2, ensure_ascii=False)}

## Propostas de Melhoria
{json.dumps(proposals, indent=2, ensure_ascii=False)}

## Resultados de Testes
{json.dumps(test_results, indent=2, ensure_ascii=False)}

## Melhorias Aplicadas
{json.dumps(applied, indent=2, ensure_ascii=False)}

## Validação
{json.dumps(validation, indent=2, ensure_ascii=False)}

## Métricas
{json.dumps(self.metrics, indent=2, ensure_ascii=False)}
"""
        
        # Salvar documentação
        doc_path = Path("docs/evolution_cycles.md")
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with doc_path.open('a', encoding='utf-8') as f:
            f.write(doc + "\n\n---\n\n")
    
    async def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Busca na memória semântica usando RAG"""
        self.logger.info(f"Buscando na memória: {query}")
        
        # Gerar embedding da query
        query_embedding = self._generate_embedding({"query": query})
        
        # Buscar soluções similares (simulado - na prática usaria busca vetorial)
        similar_solutions = []
        
        for memory_item in self.memory_embeddings:
            similarity = self._calculate_similarity(query_embedding, memory_item["embedding"])
            if similarity > 0.7:  # Threshold de similaridade
                similar_solutions.append({
                    "solution": memory_item["solution"],
                    "similarity": similarity
                })
        
        # Ordenar por similaridade
        similar_solutions.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similar_solutions[:5]  # Retornar top 5
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcula similaridade entre embeddings (cosine similarity)"""
        import math
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def add_user_feedback(self, feedback: Dict[str, Any]) -> None:
        """Adiciona feedback do usuário à memória"""
        self.logger.info("Adicionando feedback do usuário")
        
        feedback_item = {
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        self.long_term_memory["user_feedback"].append(feedback_item)
    
    async def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do agente"""
        return {
            "agent": "evolution",
            "learning_enabled": self.learning_enabled,
            "current_phase": self.current_phase.value,
            "memory_size": len(self.memory_embeddings),
            "learning_cycles": self.metrics["learning_cycles"],
            "metrics": self.metrics
        }
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da memória"""
        return {
            "total_solutions": len(self.long_term_memory["successful_solutions"]),
            "total_errors": len(self.long_term_memory["common_errors"]),
            "total_feedback": len(self.long_term_memory["user_feedback"]),
            "embedding_count": len(self.memory_embeddings),
            "learning_history_size": len(self.learning_history)
        }