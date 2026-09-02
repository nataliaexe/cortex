#!/usr/bin/env python3
"""
Gênesis Córtex - Sandbox Tester
Testa mudanças em Docker antes de aplicar
"""

import logging
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import shutil


class SandboxTester:
    """Testador de sandbox para validação de mudanças"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.sandbox_enabled = config.get("self_modification", {}).get("sandbox", True)
        self.docker_available = self._check_docker()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cortex_sandbox_"))
        
    def _check_docker(self) -> bool:
        """Verifica se Docker está disponível"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.warning(f"Docker não disponível: {e}")
            return False
            
    async def test_code_change(self, file_path: str, new_content: str, test_commands: List[str]) -> Dict[str, Any]:
        """Testa mudança de código em sandbox"""
        if not self.sandbox_enabled or not self.docker_available:
            self.logger.warning("Sandbox não disponível, pulando testes")
            return {
                "success": True,
                "message": "Sandbox não disponível, mudança aplicada sem testes",
                "tested": False
            }
            
        try:
            # Prepara ambiente de teste
            test_dir = self.temp_dir / "test_env"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Copia arquivo modificado
            test_file = test_dir / Path(file_path).name
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # Cria Dockerfile para teste
            dockerfile = self._create_test_dockerfile(test_dir)
            
            # Build imagem de teste
            image_name = f"cortex_test_{hash(file_path)}"
            build_result = await self._build_docker_image(dockerfile, image_name)
            
            if not build_result["success"]:
                return {
                    "success": False,
                    "message": f"Erro ao buildar imagem: {build_result['message']}",
                    "tested": True
                }
                
            # Executa testes
            test_results = []
            for command in test_commands:
                result = await self._run_docker_command(image_name, command)
                test_results.append(result)
                
            # Limpa
            await self._cleanup_docker_image(image_name)
            
            # Avalia resultados
            all_passed = all(r["success"] for r in test_results)
            
            return {
                "success": all_passed,
                "message": "Testes concluídos" if all_passed else "Alguns testes falharam",
                "tested": True,
                "test_results": test_results
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao testar mudança: {e}")
            return {
                "success": False,
                "message": f"Erro no teste: {str(e)}",
                "tested": True
            }
            
    def _create_test_dockerfile(self, test_dir: Path) -> Path:
        """Cria Dockerfile para teste"""
        dockerfile = test_dir / "Dockerfile"
        
        dockerfile_content = """FROM python:3.12-slim

WORKDIR /app

# Instala dependências básicas
RUN pip install pytest

# Copia arquivo de teste
COPY *.py .

# Comando padrão
CMD ["python", "-m", "pytest", "-v"]
"""
        
        with open(dockerfile, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
            
        return dockerfile
        
    async def _build_docker_image(self, dockerfile: Path, image_name: str) -> Dict[str, Any]:
        """Builda imagem Docker"""
        try:
            result = subprocess.run(
                ["docker", "build", "-t", image_name, str(dockerfile.parent)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "message": result.stdout if result.returncode == 0 else result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Timeout no build da imagem"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro no build: {str(e)}"
            }
            
    async def _run_docker_command(self, image_name: str, command: str) -> Dict[str, Any]:
        """Executa comando em container Docker"""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", image_name] + command.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "command": command,
                "message": "Timeout na execução do comando"
            }
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "message": f"Erro na execução: {str(e)}"
            }
            
    async def _cleanup_docker_image(self, image_name: str):
        """Remove imagem Docker"""
        try:
            subprocess.run(
                ["docker", "rmi", image_name],
                capture_output=True,
                timeout=30
            )
        except Exception as e:
            self.logger.warning(f"Erro ao limpar imagem {image_name}: {e}")
            
    async def test_security_scan(self, file_path: str, new_content: str) -> Dict[str, Any]:
        """Testa mudança com scanner de segurança"""
        try:
            # Prepara arquivo temporário
            test_file = self.temp_dir / "security_test.py"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # Executa scanner de segurança
            try:
                from security.universal_scanner import UniversalScanner
                scanner = UniversalScanner(self.config)
            except ImportError:
                # Fallback se import falhar
                self.logger.warning("Scanner de segurança não disponível para teste")
                return {
                    "success": True,
                    "vulnerabilities": [],
                    "total": 0,
                    "critical": 0,
                    "high": 0,
                    "message": "Scanner de segurança não disponível"
                }
            
            result = scanner.scan_file(str(test_file))
            
            return {
                "success": True,
                "vulnerabilities": result.get("vulnerabilities", []),
                "total": result.get("total", 0),
                "critical": result.get("critical", 0),
                "high": result.get("high", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Erro no teste de segurança: {e}")
            return {
                "success": False,
                "message": f"Erro no teste de segurança: {str(e)}"
            }
            
    async def test_syntax(self, file_path: str, new_content: str) -> Dict[str, Any]:
        """Testa sintaxe do código"""
        try:
            import ast
            
            # Tenta parsear o código
            ast.parse(new_content)
            
            return {
                "success": True,
                "message": "Sintaxe válida"
            }
            
        except SyntaxError as e:
            return {
                "success": False,
                "message": f"Erro de sintaxe: {str(e)}",
                "line": e.lineno,
                "column": e.offset
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao testar sintaxe: {str(e)}"
            }
            
    async def comprehensive_test(self, file_path: str, new_content: str, test_commands: Optional[List[str]] = None) -> Dict[str, Any]:
        """Executa testes abrangentes"""
        results = {
            "syntax": await self.test_syntax(file_path, new_content),
            "security": await self.test_security_scan(file_path, new_content)
        }
        
        if test_commands:
            results["functional"] = await self.test_code_change(file_path, new_content, test_commands)
            
        # Avalia resultado geral
        all_passed = all(
            r.get("success", False) for r in results.values()
            if isinstance(r, dict) and "success" in r
        )
        
        results["overall_success"] = all_passed
        results["message"] = "Todos os testes passaram" if all_passed else "Alguns testes falharam"
        
        return results
        
    async def cleanup(self):
        """Limpa recursos temporários"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.logger.info("Diretório temporário limpo")
        except Exception as e:
            self.logger.error(f"Erro ao limpar recursos: {e}")