#!/usr/bin/env python3
"""
Gênesis Córtex - Capability Discovery
Identifica lacunas no PROJETO.md e sugere melhorias
"""

import logging
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path
import re


class CapabilityDiscovery:
    """Descobridor de capacidades e lacunas"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.project_root = Path(".")
        self.project_doc = self.project_root / "PROJETO.md"
        
    async def discover_gaps(self) -> Dict[str, Any]:
        """Descobre lacunas no projeto"""
        gaps = {
            "missing_modules": [],
            "incomplete_implementations": [],
            "suggested_improvements": [],
            "code_quality_issues": []
        }
        
        # Analisa documentação do projeto
        if self.project_doc.exists():
            documented_features = self._parse_project_doc()
            implemented_features = self._analyze_implemented_features()
            
            gaps["missing_modules"] = self._find_missing_modules(documented_features, implemented_features)
            gaps["incomplete_implementations"] = self._find_incomplete_implementations()
            
        gaps["suggested_improvements"] = await self._suggest_improvements()
        gaps["code_quality_issues"] = self._analyze_code_quality()
        
        return gaps
        
    def _parse_project_doc(self) -> List[str]:
        """Parseia documentação do projeto"""
        if not self.project_doc.exists():
            return []
            
        documented_features = []
        
        try:
            with open(self.project_doc, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extrai features mencionadas no documento
            patterns = [
                r'##\s+(\w+)',  # Títulos de seções
                r'\*\*(\w+)\*\*',  # Palavras em negrito
                r'`(\w+)`',  # Código inline
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                documented_features.extend(matches)
                
        except Exception as e:
            self.logger.error(f"Erro ao parsear PROJETO.md: {e}")
            
        return list(set(documented_features))
        
    def _analyze_implemented_features(self) -> List[str]:
        """Analisa features implementadas"""
        implemented = []
        
        # Analisa arquivos Python
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extrai nomes de classes e funções
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        implemented.append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        implemented.append(node.name)
                        
            except Exception as e:
                self.logger.warning(f"Erro ao analisar {py_file}: {e}")
                
        return list(set(implemented))
        
    def _find_missing_modules(self, documented: List[str], implemented: List[str]) -> List[str]:
        """Encontra módulos documentados mas não implementados"""
        documented_lower = [d.lower() for d in documented]
        implemented_lower = [i.lower() for i in implemented]
        
        missing = []
        for doc in documented:
            if doc.lower() not in implemented_lower:
                missing.append(doc)
                
        return missing
        
    def _find_incomplete_implementations(self) -> List[Dict[str, Any]]:
        """Encontra implementações incompletas"""
        incomplete = []
        
        # Procura por TODO, FIXME, etc.
        todo_patterns = [
            r'TODO',
            r'FIXME',
            r'XXX',
            r'HACK',
            r'NOTE',
            r'pending',
            r'implementação pendente'
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    for pattern in todo_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            incomplete.append({
                                "file": str(py_file),
                                "line": i,
                                "content": line.strip(),
                                "type": pattern
                            })
                            break
                            
            except Exception as e:
                self.logger.warning(f"Erro ao analisar {py_file}: {e}")
                
        return incomplete
        
    async def _suggest_improvements(self) -> List[Dict[str, Any]]:
        """Sugere melhorias baseadas em análise"""
        suggestions = []
        
        # Analisa estrutura do projeto
        core_dir = self.project_root / "core"
        security_dir = self.project_root / "security"
        
        if not core_dir.exists():
            suggestions.append({
                "type": "structure",
                "priority": "high",
                "suggestion": "Criar diretório core com módulos principais"
            })
            
        if not security_dir.exists():
            suggestions.append({
                "type": "security",
                "priority": "high",
                "suggestion": "Criar diretório security com módulos de segurança"
            })
            
        # Analisa dependências
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            suggestions.append({
                "type": "dependencies",
                "priority": "medium",
                "suggestion": "Criar requirements.txt com dependências do projeto"
            })
            
        # Analisa testes
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists() or not list(tests_dir.glob("*.py")):
            suggestions.append({
                "type": "testing",
                "priority": "medium",
                "suggestion": "Criar testes unitários para os módulos principais"
            })
            
        # Analisa documentação
        readme_file = self.project_root / "README.md"
        if not readme_file.exists():
            suggestions.append({
                "type": "documentation",
                "priority": "medium",
                "suggestion": "Criar README.md com instruções de uso"
            })
            
        return suggestions
        
    def _analyze_code_quality(self) -> List[Dict[str, Any]]:
        """Analisa qualidade do código"""
        issues = []
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Verifica linhas muito longas
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if len(line) > 100:
                        issues.append({
                            "file": str(py_file),
                            "line": i,
                            "type": "long_line",
                            "severity": "low",
                            "message": f"Linha muito longa ({len(line)} caracteres)"
                        })
                        
                # Verifica funções muito longas
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > 50:
                            issues.append({
                                "file": str(py_file),
                                "line": node.lineno,
                                "type": "long_function",
                                "severity": "medium",
                                "message": f"Função muito longa ({func_lines} linhas)"
                            })
                            
            except Exception as e:
                self.logger.warning(f"Erro ao analisar qualidade de {py_file}: {e}")
                
        return issues
        
    async def generate_improvement_plan(self) -> Dict[str, Any]:
        """Gera plano de melhorias"""
        gaps = await self.discover_gaps()
        
        plan = {
            "priority_high": [],
            "priority_medium": [],
            "priority_low": [],
            "estimated_effort": {}
        }
        
        # Classifica por prioridade
        for item in gaps["missing_modules"]:
            plan["priority_high"].append({
                "type": "missing_module",
                "description": f"Implementar módulo: {item}",
                "effort": "medium"
            })
            
        for item in gaps["incomplete_implementations"]:
            plan["priority_high"].append({
                "type": "incomplete_implementation",
                "description": f"Completar implementação em {item['file']}:{item['line']}",
                "effort": "low"
            })
            
        for suggestion in gaps["suggested_improvements"]:
            if suggestion["priority"] == "high":
                plan["priority_high"].append(suggestion)
            elif suggestion["priority"] == "medium":
                plan["priority_medium"].append(suggestion)
            else:
                plan["priority_low"].append(suggestion)
                
        return plan