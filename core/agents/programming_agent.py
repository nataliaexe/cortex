#!/usr/bin/env python3
"""
Gênesis Córtex - Agente de Programação Autônomo
Agente especializado em desenvolvimento de software completo com ciclo autônomo
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from ..governance import Governance
from ..model_router import ModelRouter
from ..semantic_matcher import SemanticMatcher
from ..self_modification.safe_editor import SafeEditor
from ..self_modification.capability_discovery import CapabilityDiscovery
from database.repositories.task_repository import TaskRepository
from database.repositories.audit_repository import AuditRepository


class TaskStatus(Enum):
    """Status de execução de tarefa"""
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    FIXING = "fixing"
    VALIDATING = "validating"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgrammingAgent:
    """Agente de programação autônomo com ciclo completo de desenvolvimento"""
    
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
        
        # Estado do agente
        self.current_task: Optional[str] = None
        self.task_status: TaskStatus = TaskStatus.PLANNING
        self.iteration_count: int = 0
        self.max_iterations: int = 5
        self.project_path: Optional[Path] = None
        
        # Métricas
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_iterations": 0,
            "code_lines_written": 0,
            "tests_run": 0
        }
        
    async def process_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Processa uma tarefa de programação com ciclo autônomo completo"""
        context = context or {}
        task_id = datetime.now().isoformat()
        self.current_task = task
        self.iteration_count = 0
        
        self.logger.info(f"Agente de Programação: Iniciando tarefa '{task}'")
        
        try:
            # Fase 1: Planejamento
            self.task_status = TaskStatus.PLANNING
            plan = await self._plan_task(task, context)
            
            # Fase 2: Execução das subtarefas
            results = []
            for subtask in plan.get("subtasks", []):
                result = await self._execute_subtask(subtask, context)
                results.append(result)
                
                # Se falhou, tentar corrigir
                if not result.get("success"):
                    self.task_status = TaskStatus.FIXING
                    fix_result = await self._fix_issue(subtask, result, context)
                    if fix_result.get("success"):
                        results[-1] = fix_result
            
            # Fase 3: Validação final
            self.task_status = TaskStatus.VALIDATING
            validation = await self._validate_results(results, context)
            
            # Fase 4: Documentação
            self.task_status = TaskStatus.DOCUMENTING
            await self._document_solution(task, plan, results, validation)
            
            # Finalização
            self.task_status = TaskStatus.COMPLETED
            self.metrics["tasks_completed"] += 1
            
            result = {
                "task_id": task_id,
                "task": task,
                "status": "completed",
                "plan": plan,
                "results": results,
                "validation": validation,
                "metrics": self.metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            # Registrar em audit
            self.governance.audit(
                "programming_task_completed",
                self.governance.authorize("programming_task", {"task": task}, context),
                params={"task": task},
                outcome="completed"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no agente de programação: {e}")
            self.task_status = TaskStatus.FAILED
            self.metrics["tasks_failed"] += 1
            
            self.governance.audit(
                "programming_task_failed",
                self.governance.authorize("programming_task", {"task": task}, context),
                params={"task": task, "error": str(e)},
                outcome="failed"
            )
            
            return {
                "task_id": task_id,
                "task": task,
                "status": "failed",
                "error": str(e),
                "metrics": self.metrics,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _plan_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Planeja a execução da tarefa usando DeepSeek R1"""
        self.logger.info(f"Planejando tarefa: {task}")
        
        # Usar modelo de raciocínio para planejamento
        prompt = f"""
Como um desenvolvedor sênior, planeje a implementação da seguinte tarefa:

TAREFA: {task}

CONTEXTO: {json.dumps(context, indent=2)}

Forneça um plano detalhado em formato JSON com:
1. subtasks: lista de subtarefas em ordem de execução
2. files: arquivos que precisam ser criados ou modificados
3. dependencies: dependências externas necessárias
4. tests: testes que devem ser criados
5. validation: critérios de validação

Exemplo de formato:
{{
    "subtasks": [
        {{"name": "Criar estrutura de diretórios", "action": "create_directory", "params": {{"path": "src"}}}},
        {{"name": "Criar arquivo principal", "action": "write_file", "params": {{"path": "src/main.py", "content": "..."}}}}
    ],
    "files": ["src/main.py", "src/utils.py"],
    "dependencies": ["numpy", "pandas"],
    "tests": ["tests/test_main.py"],
    "validation": ["Executar pytest", "Verificar funcionalidade"]
}}
"""
        
        try:
            response = await self.model_router.route_request(
                prompt=prompt,
                task_type="reasoning"
            )
            
            # Tentar extrair JSON da resposta
            plan = self._extract_json(response)
            
            if not plan:
                # Fallback para plano básico
                plan = {
                    "subtasks": [
                        {"name": "Analisar requisitos", "action": "analyze", "params": {}},
                        {"name": "Implementar solução", "action": "implement", "params": {}},
                        {"name": "Testar", "action": "test", "params": {}}
                    ],
                    "files": [],
                    "dependencies": [],
                    "tests": [],
                    "validation": []
                }
            
            self.logger.info(f"Plano gerado: {len(plan.get('subtasks', []))} subtarefas")
            return plan
            
        except Exception as e:
            self.logger.error(f"Erro ao planejar tarefa: {e}")
            return {"subtasks": [], "files": [], "dependencies": [], "tests": [], "validation": []}
    
    async def _execute_subtask(self, subtask: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma subtarefa específica"""
        self.logger.info(f"Executando subtarefa: {subtask.get('name')}")
        self.task_status = TaskStatus.CODING
        self.iteration_count += 1
        self.metrics["total_iterations"] += 1
        
        action = subtask.get("action")
        params = subtask.get("params", {})
        
        try:
            if action == "create_directory":
                return await self._create_directory(params)
            elif action == "write_file":
                return await self._write_file(params)
            elif action == "read_file":
                return await self._read_file(params)
            elif action == "run_code":
                return await self._run_code(params)
            elif action == "run_tests":
                return await self._run_tests(params)
            elif action == "git_commit":
                return await self._git_commit(params)
            elif action == "install_dependencies":
                return await self._install_dependencies(params)
            else:
                # Ação genérica - delegar para Qwen Coder
                return await self._execute_with_coder(subtask, context)
                
        except Exception as e:
            self.logger.error(f"Erro ao executar subtarefa {subtask.get('name')}: {e}")
            return {
                "subtask": subtask.get("name"),
                "success": False,
                "error": str(e)
            }
    
    async def _create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um diretório"""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Caminho não especificado"}
        
        try:
            dir_path = self.governance.ensure_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(dir_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Escreve um arquivo usando SafeEditor"""
        path = params.get("path")
        content = params.get("content", "")
        
        if not path:
            return {"success": False, "error": "Caminho não especificado"}
        
        try:
            result = self.safe_editor.write_file(path, content)
            self.metrics["code_lines_written"] += len(content.split('\n'))
            return {"success": True, "path": result["path"], "backup": result.get("backup")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lê um arquivo"""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Caminho não especificado"}
        
        try:
            file_path = self.governance.ensure_path(path, must_exist=True)
            content = file_path.read_text(encoding='utf-8')
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa código"""
        code = params.get("code", "")
        language = params.get("language", "python")
        
        if not code:
            return {"success": False, "error": "Código não especificado"}
        
        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {"success": False, "error": f"Linguagem {language} não suportada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa testes"""
        test_path = params.get("path", ".")
        
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.metrics["tests_run"] += 1
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _git_commit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Faz commit no git"""
        message = params.get("message", "Update from Programming Agent")
        
        try:
            subprocess.run(["git", "add", "."], timeout=10, check=True)
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"success": True, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _install_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Instala dependências"""
        dependencies = params.get("dependencies", [])
        
        if not dependencies:
            return {"success": True, "message": "Nenhuma dependência para instalar"}
        
        try:
            for dep in dependencies:
                subprocess.run(
                    ["pip", "install", dep],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            return {"success": True, "installed": dependencies}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_with_coder(self, subtask: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa subtarefa usando Qwen Coder"""
        prompt = f"""
Como um programador especialista, execute a seguinte subtarefa:

SUBTAREFA: {subtask.get('name')}
DESCRIÇÃO: {subtask.get('description', '')}
PARÂMETROS: {json.dumps(subtask.get('params', {}), indent=2)}

Forneça o código necessário e explique como executar.
"""
        
        try:
            response = await self.model_router.route_request(
                prompt=prompt,
                task_type="coding"
            )
            
            # Extrair código da resposta
            code = self._extract_code(response)
            
            if code:
                # Salvar código temporariamente
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                # Executar código
                result = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Limpar arquivo temporário
                Path(temp_file).unlink(missing_ok=True)
                
                return {
                    "success": result.returncode == 0,
                    "code": code,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {"success": False, "error": "Não foi possível extrair código da resposta"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _fix_issue(self, subtask: Dict[str, Any], result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Tenta corrigir um erro automaticamente"""
        self.logger.info(f"Tentando corrigir erro na subtarefa: {subtask.get('name')}")
        
        if self.iteration_count >= self.max_iterations:
            return {"success": False, "error": "Máximo de iterações atingido"}
        
        error_msg = result.get("error", result.get("stderr", ""))
        
        prompt = f"""
O seguinte código falhou com o erro: {error_msg}

Subtarefa: {subtask.get('name')}
Código: {result.get('code', '')}

Analise o erro e forneça a versão corrigida do código.
"""
        
        try:
            response = await self.model_router.route_request(
                prompt=prompt,
                task_type="coding"
            )
            
            corrected_code = self._extract_code(response)
            
            if corrected_code:
                # Executar código corrigido
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(corrected_code)
                    temp_file = f.name
                
                result = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                Path(temp_file).unlink(missing_ok=True)
                
                return {
                    "success": result.returncode == 0,
                    "code": corrected_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "fixed": True
                }
            else:
                return {"success": False, "error": "Não foi possível gerar correção"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _validate_results(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Valida os resultados da execução"""
        self.logger.info("Validando resultados...")
        
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        
        validation = {
            "total_subtasks": total_count,
            "successful_subtasks": success_count,
            "failed_subtasks": total_count - success_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "all_passed": success_count == total_count
        }
        
        return validation
    
    async def _document_solution(self, task: str, plan: Dict[str, Any], results: List[Dict[str, Any]], validation: Dict[str, Any]) -> None:
        """Documenta a solução implementada"""
        self.logger.info("Documentando solução...")
        
        doc = f"""
# Documentação da Tarefa: {task}

## Data: {datetime.now().isoformat()}

## Plano de Execução
{json.dumps(plan, indent=2, ensure_ascii=False)}

## Resultados
{json.dumps(results, indent=2, ensure_ascii=False)}

## Validação
{json.dumps(validation, indent=2, ensure_ascii=False)}

## Métricas
- Subtarefas totais: {validation['total_subtasks']}
- Subtarefas bem-sucedidas: {validation['successful_subtasks']}
- Taxa de sucesso: {validation['success_rate']:.2%}
"""
        
        # Salvar documentação
        doc_path = Path("docs/programming_agent_tasks.md")
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with doc_path.open('a', encoding='utf-8') as f:
            f.write(doc + "\n\n---\n\n")
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrai JSON de um texto"""
        try:
            # Procurar por blocos JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        return None
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extrai código de um texto (blocos ```python``` ou ```código```)"""
        import re
        
        # Tentar extrair blocos de código
        patterns = [
            r'```python\n(.*?)```',
            r'```código\n(.*?)```',
            r'```\n(.*?)```'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                return matches[0].strip()
        
        return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Retorna o status atual do agente"""
        return {
            "agent": "programming",
            "current_task": self.current_task,
            "status": self.task_status.value,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
            "metrics": self.metrics
        }
    
    async def get_project_structure(self, path: str = ".") -> Dict[str, Any]:
        """Retorna a estrutura de arquivos do projeto"""
        project_path = Path(path)
        if not project_path.exists():
            return {"error": "Path não existe"}
        
        structure = {}
        
        for item in project_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(project_path)
                parent = str(relative_path.parent)
                if parent == ".":
                    parent = "root"
                
                if parent not in structure:
                    structure[parent] = []
                
                structure[parent].append(item.name)
        
        return structure
    
    async def run_git_status(self) -> Dict[str, Any]:
        """Executa git status e retorna resultado estruturado"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            files = []
            for line in result.stdout.split('\n'):
                if line:
                    status, path = line[:2], line[3:]
                    files.append({"status": status, "path": path})
            
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_git_log(self, limit: int = 10) -> Dict[str, Any]:
        """Executa git log e retorna histórico"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            commits = []
            for line in result.stdout.split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        })
            
            return {"success": True, "commits": commits}
        except Exception as e:
            return {"success": False, "error": str(e)}