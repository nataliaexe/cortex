#!/usr/bin/env python3
"""
Gênesis Córtex - Universal Security Scanner
Scanner multi-linguagem usando AST e tree-sitter
"""

import logging
import ast
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib
from datetime import datetime


class UniversalScanner:
    """Scanner universal de vulnerabilidades"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.rules_dir = Path(config.get("security", {}).get("scanner", {}).get("rules_path", "security/rules"))
        self.rules = {}
        self._load_rules()
        
    def _load_rules(self):
        """Carrega regras de segurança"""
        try:
            if not self.rules_dir.exists():
                self.logger.warning(f"Diretório de regras {self.rules_dir} não encontrado")
                return
                
            for rule_file in self.rules_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(rule_file, 'r', encoding='utf-8') as f:
                        language_rules = yaml.safe_load(f)
                        if language_rules:
                            self.rules.update(language_rules)
                            self.logger.info(f"Regras carregadas de {rule_file.name}")
                except Exception as e:
                    self.logger.error(f"Erro ao carregar regras de {rule_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Erro ao carregar regras: {e}")
            
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Escaneia um arquivo específico"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": f"Arquivo {file_path} não encontrado"}
            
        # Determina linguagem pela extensão
        language = self._detect_language(file_path)
        
        if not language:
            return {"error": f"Linguagem não suportada para {file_path.suffix}"}
            
        # Lê conteúdo do arquivo
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Erro ao ler arquivo: {e}"}
            
        # Calcula hash do arquivo
        file_hash = self._calculate_hash(file_path)
        
        # Escaneia conforme linguagem
        vulnerabilities = []
        
        if language == "python":
            vulnerabilities = self._scan_python(content, file_path)
        elif language == "javascript":
            vulnerabilities = self._scan_javascript(content, file_path)
        elif language == "java":
            vulnerabilities = self._scan_java(content, file_path)
        elif language in ["c", "cpp"]:
            vulnerabilities = self._scan_c_cpp(content, file_path)
        elif language == "go":
            vulnerabilities = self._scan_go(content, file_path)
        elif language == "rust":
            vulnerabilities = self._scan_rust(content, file_path)
        elif language == "assembly":
            vulnerabilities = self._scan_assembly(content, file_path)
            
        return {
            "file": str(file_path),
            "language": language,
            "hash": file_hash,
            "vulnerabilities": vulnerabilities,
            "total": len(vulnerabilities),
            "critical": len([v for v in vulnerabilities if v["severity"] == "critical"]),
            "high": len([v for v in vulnerabilities if v["severity"] == "high"]),
            "medium": len([v for v in vulnerabilities if v["severity"] == "medium"]),
            "low": len([v for v in vulnerabilities if v["severity"] == "low"])
        }
        
    def scan_directory(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """Escaneia um diretório inteiro"""
        directory = Path(directory)
        
        if not directory.exists():
            return {"error": f"Diretório {directory} não encontrado"}
            
        results = []
        total_vulnerabilities = 0
        total_critical = 0
        total_high = 0
        total_medium = 0
        total_low = 0
        
        # Encontra arquivos para escanear
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")
            
        for file_path in files:
            if file_path.is_file() and self._detect_language(file_path):
                result = self.scan_file(str(file_path))
                if "error" not in result:
                    results.append(result)
                    total_vulnerabilities += result["total"]
                    total_critical += result["critical"]
                    total_high += result["high"]
                    total_medium += result["medium"]
                    total_low += result["low"]
                    
        return {
            "directory": str(directory),
            "files_scanned": len(results),
            "total_vulnerabilities": total_vulnerabilities,
            "critical": total_critical,
            "high": total_high,
            "medium": total_medium,
            "low": total_low,
            "results": results,
            "scan_time": datetime.now().isoformat()
        }
        
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detecta linguagem pela extensão do arquivo"""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "javascript",
            ".jsx": "javascript",
            ".tsx": "javascript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".go": "go",
            ".rs": "rust",
            ".asm": "assembly",
            ".s": "assembly",
            ".S": "assembly"
        }
        return extensions.get(file_path.suffix.lower())
        
    def _calculate_hash(self, file_path: Path) -> str:
        """Calcula SHA-256 do arquivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def _scan_python(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código Python"""
        vulnerabilities = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Detecta uso de eval
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "eval":
                        vulnerabilities.append({
                            "type": "dangerous_function",
                            "severity": "critical",
                            "line": node.lineno,
                            "description": "Uso de eval() pode executar código arbitrário",
                            "rule": "python_eval"
                        })
                        
                    # Detecta uso de exec
                    if isinstance(node.func, ast.Name) and node.func.id == "exec":
                        vulnerabilities.append({
                            "type": "dangerous_function",
                            "severity": "critical",
                            "line": node.lineno,
                            "description": "Uso de exec() pode executar código arbitrário",
                            "rule": "python_exec"
                        })
                        
                    # Detecta uso de pickle.loads
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == "loads" and isinstance(node.func.value, ast.Name):
                            if node.func.value.id == "pickle":
                                vulnerabilities.append({
                                    "type": "dangerous_deserialization",
                                    "severity": "critical",
                                    "line": node.lineno,
                                    "description": "pickle.loads() pode executar código arbitrário",
                                    "rule": "python_pickle"
                                })
                                
                # Detecta imports perigosos
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ["pickle", "subprocess", "os"]:
                            vulnerabilities.append({
                                "type": "dangerous_import",
                                "severity": "medium",
                                "line": node.lineno,
                                "description": f"Import de {alias.name} requer cuidados adicionais",
                                "rule": f"python_import_{alias.name}"
                            })
                            
        except SyntaxError as e:
            self.logger.warning(f"Erro ao parsear Python em {file_path}: {e}")
            
        return vulnerabilities
        
    def _scan_javascript(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código JavaScript"""
        vulnerabilities = []
        
        # Análise simples baseada em regex (pode ser melhorada com ESLint)
        import re
        
        # Detecta eval
        if re.search(r'\beval\s*\(', content):
            vulnerabilities.append({
                "type": "dangerous_function",
                "severity": "critical",
                "line": 0,
                "description": "Uso de eval() pode executar código arbitrário",
                "rule": "javascript_eval"
            })
            
        # Detecta innerHTML sem sanitização
        if re.search(r'\.innerHTML\s*=', content):
            vulnerabilities.append({
                "type": "xss",
                "severity": "high",
                "line": 0,
                "description": "innerHTML pode causar XSS se não sanitizado",
                "rule": "javascript_innerhtml"
            })
            
        # Detecta document.write
        if re.search(r'document\.write\s*\(', content):
            vulnerabilities.append({
                "type": "xss",
                "severity": "high",
                "line": 0,
                "description": "document.write pode causar XSS",
                "rule": "javascript_document_write"
            })
            
        return vulnerabilities
        
    def _scan_java(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código Java"""
        vulnerabilities = []
        
        # Análise simples baseada em regex
        import re
        
        # Detecta SQL injection potencial
        if re.search(r'Statement.*execute\s*\(', content):
            vulnerabilities.append({
                "type": "sql_injection",
                "severity": "high",
                "line": 0,
                "description": "Uso de Statement pode permitir SQL injection",
                "rule": "java_statement"
            })
            
        # Detecta hashCode em passwords
        if re.search(r'password.*hashCode', content, re.IGNORECASE):
            vulnerabilities.append({
                "type": "weak_hash",
                "severity": "medium",
                "line": 0,
                "description": "hashCode não é adequado para hash de senhas",
                "rule": "java_password_hashcode"
            })
            
        return vulnerabilities
        
    def _scan_c_cpp(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código C/C++"""
        vulnerabilities = []
        
        import re
        
        # Detecta strcpy
        if re.search(r'\bstrcpy\s*\(', content):
            vulnerabilities.append({
                "type": "buffer_overflow",
                "severity": "high",
                "line": 0,
                "description": "strcpy é vulnerável a buffer overflow",
                "rule": "c_strcpy"
            })
            
        # Detecta sprintf
        if re.search(r'\bsprintf\s*\(', content):
            vulnerabilities.append({
                "type": "buffer_overflow",
                "severity": "high",
                "line": 0,
                "description": "sprintf é vulnerável a buffer overflow",
                "rule": "c_sprintf"
            })
            
        # Detecta gets
        if re.search(r'\bgets\s*\(', content):
            vulnerabilities.append({
                "type": "buffer_overflow",
                "severity": "critical",
                "line": 0,
                "description": "gets é extremamente vulnerável a buffer overflow",
                "rule": "c_gets"
            })
            
        # Detecta format string vulnerabilities
        if re.search(r'printf\s*\(\s*\w+\s*\)', content):
            vulnerabilities.append({
                "type": "format_string",
                "severity": "medium",
                "line": 0,
                "description": "printf com variável pode causar format string vulnerability",
                "rule": "c_format_string"
            })
            
        return vulnerabilities
        
    def _scan_go(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código Go"""
        vulnerabilities = []
        
        import re
        
        # Detecta exec.Command
        if re.search(r'exec\.Command\s*\(', content):
            vulnerabilities.append({
                "type": "command_injection",
                "severity": "high",
                "line": 0,
                "description": "exec.Command pode permitir command injection",
                "rule": "go_exec_command"
            })
            
        return vulnerabilities
        
    def _scan_rust(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código Rust"""
        vulnerabilities = []
        
        import re
        
        # Detecta unsafe block
        if re.search(r'\bunsafe\b', content):
            vulnerabilities.append({
                "type": "unsafe_code",
                "severity": "medium",
                "line": 0,
                "description": "Código unsafe requer validação manual",
                "rule": "rust_unsafe"
            })
            
        # Detecta unwrap
        if re.search(r'\.unwrap\s*\(\)', content):
            vulnerabilities.append({
                "type": "panic_risk",
                "severity": "low",
                "line": 0,
                "description": "unwrap pode causar panic",
                "rule": "rust_unwrap"
            })
            
        return vulnerabilities
        
    def _scan_assembly(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Escaneia código Assembly"""
        vulnerabilities = []
        
        import re
        
        # Detecta syscalls perigosas
        dangerous_syscalls = ["int 0x80", "syscall", "ret"]
        for syscall in dangerous_syscalls:
            if re.search(syscall, content):
                vulnerabilities.append({
                    "type": "dangerous_syscall",
                    "severity": "medium",
                    "line": 0,
                    "description": f"Syscall {syscall} requer análise cuidadosa",
                    "rule": f"assembly_{syscall.replace(' ', '_')}"
                })
                
        return vulnerabilities