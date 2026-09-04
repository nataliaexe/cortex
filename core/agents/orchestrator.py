#!/usr/bin/env python3
"""
Gênesis Córtex - Orquestrador de Agentes
Coordena a execução de múltiplos agentes autônomos
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ..governance import Governance
from ..semantic_matcher import SemanticMatcher
from .programming_agent import ProgrammingAgent
from .security_agent import SecurityAgent
from .evolution_agent import EvolutionAgent
from database.repositories.task_repository import TaskRepository
from database.repositories.audit_repository import AuditRepository
from database.repositories.scan_repository import ScanRepository


class AgentType(Enum):
    """Tipos de agentes disponíveis"""
    ASSISTANT = "assistant"
    PROGRAMMING = "programming"
    SECURITY = "security"
    EVOLUTION = "evolution"


class TaskPriority(Enum):
    """Prioridades de tarefa"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Status de tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Representação de uma tarefa no orquestrador"""
    task_id: str
    agent: AgentType
    action: str
    payload: Dict[str, Any]
    priority: TaskPriority
    dependencies: List[str]
    status: TaskStatus
    result: Optional[Dict[str, Any]]
    timestamp: str
    created_at: str
    updated_at: str


class AgentOrchestrator:
    """Orquestrador central de agentes autônomos"""
    
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
        
        # Sistemas centrais
        self.governance = Governance(config)
        self.semantic_matcher = SemanticMatcher(config)
        
        # Inicializar agentes
        self.programming_agent = ProgrammingAgent(config, task_repository, audit_repository)
        self.security_agent = SecurityAgent(config, task_repository, audit_repository, scan_repository)
        self.evolution_agent = EvolutionAgent(config, task_repository, audit_repository)
        
        # Fila de tarefas
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        
        # Status dos agentes
        self.agent_status = {
            AgentType.ASSISTANT: {"status": "online", "current_task": None},
            AgentType.PROGRAMMING: {"status": "idle", "current_task": None},
            AgentType.SECURITY: {"status": "idle", "current_task": None},
            AgentType.EVOLUTION: {"status": "idle", "current_task": None}
        }
        
        # Métricas do orquestrador
        self.metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "tasks_by_agent": {
                AgentType.ASSISTANT.value: 0,
                AgentType.PROGRAMMING.value: 0,
                AgentType.SECURITY.value: 0,
                AgentType.EVOLUTION.value: 0
            }
        }
        
        # Lock para operações concorrentes
        self.queue_lock = asyncio.Lock()
        
    async def submit_task(
        self,
        task_description: str,
        parameters: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Submete uma tarefa para processamento"""
        parameters = parameters or {}
        context = context or {}
        
        self.logger.info(f"Recebendo tarefa: {task_description}")
        
        # Classificar a tarefa
        agent_type = await self._classify_task(task_description, context)
        
        # Criar objeto de tarefa
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        task = Task(
            task_id=task_id,
            agent=agent_type,
            action="execute",
            payload={
                "description": task_description,
                "parameters": parameters,
                "context": context
            },
            priority=priority,
            dependencies=[],
            status=TaskStatus.PENDING,
            result=None,
            timestamp=now,
            created_at=now,
            updated_at=now
        )
        
        # Adicionar à fila
        async with self.queue_lock:
            self.task_queue.append(task)
            self.metrics["total_tasks"] += 1
            self.metrics["tasks_by_agent"][agent_type.value] += 1
        
        # Auditoria
        self.governance.audit(
            "task_submitted",
            self.governance.authorize("task_submit", {"task": task_description}, context),
            params={"task_id": task_id, "agent": agent_type.value, "description": task_description},
            outcome="submitted"
        )
        
        self.logger.info(f"Tarefa {task_id} submetida para agente {agent_type.value}")
        
        return {
            "task_id": task_id,
            "agent": agent_type.value,
            "status": "pending",
            "priority": priority.value,
            "timestamp": now
        }
    
    async def _classify_task(self, task_description: str, context: Dict[str, Any]) -> AgentType:
        """Classifica a tarefa para o agente apropriado"""
        self.logger.info(f"Classificando tarefa: {task_description}")
        
        # Usar SemanticMatcher para classificação
        classification = await self.semantic_matcher.match_intent(task_description, context)
        
        # Mapear intenções para agentes
        intent_to_agent = {
            "programming": AgentType.PROGRAMMING,
            "coding": AgentType.PROGRAMMING,
            "development": AgentType.PROGRAMMING,
            "debug": AgentType.PROGRAMMING,
            "security": AgentType.SECURITY,
            "scan": AgentType.SECURITY,
            "pentest": AgentType.SECURITY,
            "monitor": AgentType.SECURITY,
            "evolution": AgentType.EVOLUTION,
            "learning": AgentType.EVOLUTION,
            "improvement": AgentType.EVOLUTION,
            "system": AgentType.ASSISTANT,
            "automation": AgentType.ASSISTANT,
            "general": AgentType.ASSISTANT
        }
        
        # Determinar agente baseado na classificação
        matched_intent = classification.get("intent", "general")
        agent_type = intent_to_agent.get(matched_intent, AgentType.ASSISTANT)
        
        self.logger.info(f"Tarefa classificada como {matched_intent} -> agente {agent_type.value}")
        
        return agent_type
    
    async def process_queue(self) -> None:
        """Processa a fila de tarefas continuamente"""
        self.logger.info("Iniciando processamento da fila de tarefas")
        
        while True:
            try:
                # Verificar se há tarefas pendentes
                async with self.queue_lock:
                    if not self.task_queue:
                        await asyncio.sleep(1)
                        continue
                    
                    # Obter próxima tarefa (prioridade alta primeiro)
                    self.task_queue.sort(key=lambda t: self._priority_value(t.priority))
                    task = self.task_queue.pop(0)
                
                # Verificar dependências
                if not await self._check_dependencies(task):
                    self.logger.info(f"Tarefa {task.task_id} aguardando dependências")
                    async with self.queue_lock:
                        self.task_queue.append(task)  # Recolocar no final da fila
                    await asyncio.sleep(5)
                    continue
                
                # Executar tarefa
                await self._execute_task(task)
                
            except Exception as e:
                self.logger.error(f"Erro no processamento da fila: {e}")
                await asyncio.sleep(5)
    
    def _priority_value(self, priority: TaskPriority) -> int:
        """Converte prioridade para valor numérico para ordenação"""
        values = {
            TaskPriority.HIGH: 0,
            TaskPriority.MEDIUM: 1,
            TaskPriority.LOW: 2
        }
        return values.get(priority, 1)
    
    async def _check_dependencies(self, task: Task) -> bool:
        """Verifica se dependências da tarefa foram satisfeitas"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if self.completed_tasks[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def _execute_task(self, task: Task) -> None:
        """Executa uma tarefa específica"""
        self.logger.info(f"Executando tarefa {task.task_id} com agente {task.agent.value}")
        
        # Atualizar status
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.now().isoformat()
        self.active_tasks[task.task_id] = task
        
        # Atualizar status do agente
        self.agent_status[task.agent]["status"] = "busy"
        self.agent_status[task.agent]["current_task"] = task.task_id
        
        try:
            # Executar com o agente apropriado
            if task.agent == AgentType.PROGRAMMING:
                result = await self.programming_agent.process_task(
                    task.payload["description"],
                    task.payload["context"]
                )
            elif task.agent == AgentType.SECURITY:
                # Determinar modo de segurança
                action = task.payload.get("action", "scan")
                if action == "scan":
                    result = await self.security_agent.execute_scan(
                        task.payload["parameters"].get("target", "."),
                        task.payload["parameters"].get("scan_type", "full")
                    )
                elif action == "monitor":
                    result = await self.security_agent.start_monitoring(
                        task.payload["parameters"].get("targets")
                    )
                elif action == "pentest":
                    result = await self.security_agent.execute_pentest(
                        task.payload["parameters"].get("target", "."),
                        task.payload["parameters"].get("scope")
                    )
                else:
                    result = {"error": f"Unknown security action: {action}"}
            elif task.agent == AgentType.EVOLUTION:
                action = task.payload.get("action", "learning_cycle")
                if action == "learning_cycle":
                    result = await self.evolution_agent.run_learning_cycle()
                elif action == "enable_learning":
                    result = await self.evolution_agent.enable_learning()
                elif action == "disable_learning":
                    result = await self.evolution_agent.disable_learning()
                else:
                    result = {"error": f"Unknown evolution action: {action}"}
            else:  # ASSISTANT
                # Tarefas gerais são tratadas pelo motor principal
                result = {
                    "message": f"Tarefa assistencial: {task.payload['description']}",
                    "status": "completed"
                }
            
            # Atualizar resultado
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now().isoformat()
            
            # Atualizar métricas
            self.metrics["completed_tasks"] += 1
            
            # Auditoria
            self.governance.audit(
                "task_completed",
                self.governance.authorize("task_complete", {"task_id": task.task_id}, {}),
                params={"task_id": task.task_id, "agent": task.agent.value},
                outcome="completed"
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao executar tarefa {task.task_id}: {e}")
            
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}
            task.updated_at = datetime.now().isoformat()
            
            self.metrics["failed_tasks"] += 1
            
            # Auditoria
            self.governance.audit(
                "task_failed",
                self.governance.authorize("task_complete", {"task_id": task.task_id}, {}),
                params={"task_id": task.task_id, "error": str(e)},
                outcome="failed"
            )
        
        finally:
            # Mover para completed
            self.completed_tasks[task.task_id] = task
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            # Liberar agente
            self.agent_status[task.agent]["status"] = "idle"
            self.agent_status[task.agent]["current_task"] = None
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancela uma tarefa"""
        self.logger.info(f"Cancelando tarefa {task_id}")
        
        # Verificar se tarefa está na fila
        async with self.queue_lock:
            for i, task in enumerate(self.task_queue):
                if task.task_id == task_id:
                    task.status = TaskStatus.CANCELLED
                    self.task_queue.pop(i)
                    self.metrics["cancelled_tasks"] += 1
                    
                    self.governance.audit(
                        "task_cancelled",
                        self.governance.authorize("task_cancel", {"task_id": task_id}, {}),
                        params={"task_id": task_id},
                        outcome="cancelled"
                    )
                    
                    return {"task_id": task_id, "status": "cancelled"}
        
        # Verificar se tarefa está ativa
        if task_id in self.active_tasks:
            # Não podemos cancelar tarefas em execução facilmente
            return {
                "task_id": task_id,
                "status": "running",
                "message": "Cannot cancel running task"
            }
        
        return {"task_id": task_id, "status": "not_found"}
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Retorna status de uma tarefa específica"""
        # Verificar na fila
        async with self.queue_lock:
            for task in self.task_queue:
                if task.task_id == task_id:
                    return asdict(task)
        
        # Verificar nas ativas
        if task_id in self.active_tasks:
            return asdict(self.active_tasks[task_id])
        
        # Verificar nas completadas
        if task_id in self.completed_tasks:
            return asdict(self.completed_tasks[task_id])
        
        return {"task_id": task_id, "status": "not_found"}
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Retorna status da fila de tarefas"""
        async with self.queue_lock:
            pending = [asdict(t) for t in self.task_queue]
        
        active = [asdict(t) for t in self.active_tasks.values()]
        recent_completed = [asdict(t) for t in list(self.completed_tasks.values())[-10:]]
        
        return {
            "pending_count": len(pending),
            "pending_tasks": pending,
            "active_count": len(active),
            "active_tasks": active,
            "recent_completed": recent_completed,
            "metrics": self.metrics
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Retorna status de todos os agentes"""
        return {
            "agents": {
                agent_type.value: status
                for agent_type, status in self.agent_status.items()
            },
            "programming_agent": await self.programming_agent.get_status(),
            "security_agent": await self.security_agent.get_status(),
            "evolution_agent": await self.evolution_agent.get_status()
        }
    
    async def coordinate_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Coordena execução paralela de múltiplas tarefas"""
        self.logger.info(f"Coordenando {len(tasks)} tarefas em paralelo")
        
        # Submeter todas as tarefas
        task_ids = []
        for task_spec in tasks:
            result = await self.submit_task(
                task_spec.get("description"),
                task_spec.get("parameters"),
                TaskPriority(task_spec.get("priority", "medium")),
                task_spec.get("context")
            )
            task_ids.append(result["task_id"])
        
        # Aguardar conclusão de todas
        results = {}
        for task_id in task_ids:
            # Aguardar com timeout
            for _ in range(60):  # 60 segundos máximo
                status = await self.get_task_status(task_id)
                if status["status"] in ["completed", "failed", "cancelled"]:
                    results[task_id] = status
                    break
                await asyncio.sleep(1)
            else:
                results[task_id] = {"status": "timeout"}
        
        return {
            "total_tasks": len(tasks),
            "completed": sum(1 for r in results.values() if r["status"] == "completed"),
            "failed": sum(1 for r in results.values() if r["status"] == "failed"),
            "results": results
        }
    
    async def suggest_agent_switch(self, current_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sugere troca para agente especializado"""
        self.logger.info(f"Analisando se deve sugerir troca de agente para: {current_task}")
        
        # Classificar tarefa atual
        suggested_agent = await self._classify_task(current_task, context)
        
        # Se não for assistant, sugerir troca
        if suggested_agent != AgentType.ASSISTANT:
            return {
                "suggest_switch": True,
                "current_agent": "assistant",
                "suggested_agent": suggested_agent.value,
                "reason": f"Task better suited for {suggested_agent.value} agent",
                "message": f"Esta tarefa pode ser melhor tratada pelo agente de {suggested_agent.value}. Deseja continuar com este agente especializado?"
            }
        
        return {
            "suggest_switch": False,
            "current_agent": "assistant",
            "reason": "Task is appropriate for current agent"
        }
    
    async def generate_report(self) -> Dict[str, Any]:
        """Gera relatório de atividades do orquestrador"""
        self.logger.info("Gerando relatório do orquestrador")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "agent_status": await self.get_agent_status(),
            "queue_status": await self.get_queue_status(),
            "recent_activity": list(self.completed_tasks.values())[-20:]
        }
        
        return report
    
    async def cleanup(self) -> None:
        """Limpa recursos do orquestrador"""
        self.logger.info("Limpando recursos do orquestrador")
        
        # Parar monitoramento de segurança se ativo
        if self.agent_status[AgentType.SECURITY]["status"] == "busy":
            await self.security_agent.stop_monitoring()
        
        # Limpar tarefas pendentes
        async with self.queue_lock:
            self.task_queue.clear()
        
        self.logger.info("Orquestrador finalizado")