#!/usr/bin/env python3
"""
Gênesis Córtex - Dependency Checker
Verificação de dependências usando OSV (Open Source Vulnerabilities)
"""

import logging
import json
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import re


class DependencyChecker:
    """Verificador de dependências para CVEs conhecidas"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.osv_api_url = "https://api.osv.dev/v1"
        self.cache_dir = Path("data/osv_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def check_python(self, requirements_path: str) -> Dict[str, Any]:
        """Verifica dependências Python (requirements.txt)"""
        requirements_path = Path(requirements_path)
        
        if not requirements_path.exists():
            return {"error": f"Arquivo {requirements_path} não encontrado"}
            
        # Parse requirements.txt
        dependencies = self._parse_requirements(requirements_path)
        
        if not dependencies:
            return {"error": "Nenhuma dependência encontrada"}
            
        # Verifica cada dependência
        results = []
        total_vulnerabilities = 0
        
        for package, version in dependencies.items():
            vulns = self._check_osv(package, version, "pypi")
            if vulns:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": vulns,
                    "count": len(vulns)
                })
                total_vulnerabilities += len(vulns)
            else:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": [],
                    "count": 0
                })
                
        return {
            "ecosystem": "Python",
            "file": str(requirements_path),
            "dependencies_checked": len(dependencies),
            "total_vulnerabilities": total_vulnerabilities,
            "results": results,
            "check_time": datetime.now().isoformat()
        }
        
    def check_javascript(self, package_json_path: str) -> Dict[str, Any]:
        """Verifica dependências JavaScript (package.json)"""
        package_json_path = Path(package_json_path)
        
        if not package_json_path.exists():
            return {"error": f"Arquivo {package_json_path} não encontrado"}
            
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                
        except Exception as e:
            return {"error": f"Erro ao ler package.json: {e}"}
            
        # Extrai dependências
        dependencies = {}
        dependencies.update(package_data.get("dependencies", {}))
        dependencies.update(package_data.get("devDependencies", {}))
        
        if not dependencies:
            return {"error": "Nenhuma dependência encontrada"}
            
        # Verifica cada dependência
        results = []
        total_vulnerabilities = 0
        
        for package, version in dependencies.items():
            # Remove prefix ^ ou ~
            clean_version = version.lstrip("^~")
            vulns = self._check_osv(package, clean_version, "npm")
            if vulns:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": vulns,
                    "count": len(vulns)
                })
                total_vulnerabilities += len(vulns)
            else:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": [],
                    "count": 0
                })
                
        return {
            "ecosystem": "JavaScript",
            "file": str(package_json_path),
            "dependencies_checked": len(dependencies),
            "total_vulnerabilities": total_vulnerabilities,
            "results": results,
            "check_time": datetime.now().isoformat()
        }
        
    def check_go(self, go_mod_path: str) -> Dict[str, Any]:
        """Verifica dependências Go (go.mod)"""
        go_mod_path = Path(go_mod_path)
        
        if not go_mod_path.exists():
            return {"error": f"Arquivo {go_mod_path} não encontrado"}
            
        # Parse go.mod
        dependencies = self._parse_go_mod(go_mod_path)
        
        if not dependencies:
            return {"error": "Nenhuma dependência encontrada"}
            
        # Verifica cada dependência
        results = []
        total_vulnerabilities = 0
        
        for package, version in dependencies.items():
            vulns = self._check_osv(package, version, "Go")
            if vulns:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": vulns,
                    "count": len(vulns)
                })
                total_vulnerabilities += len(vulns)
            else:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": [],
                    "count": 0
                })
                
        return {
            "ecosystem": "Go",
            "file": str(go_mod_path),
            "dependencies_checked": len(dependencies),
            "total_vulnerabilities": total_vulnerabilities,
            "results": results,
            "check_time": datetime.now().isoformat()
        }
        
    def check_rust(self, cargo_toml_path: str) -> Dict[str, Any]:
        """Verifica dependências Rust (Cargo.toml)"""
        cargo_toml_path = Path(cargo_toml_path)
        
        if not cargo_toml_path.exists():
            return {"error": f"Arquivo {cargo_toml_path} não encontrado"}
            
        try:
            import toml
            with open(cargo_toml_path, 'r', encoding='utf-8') as f:
                cargo_data = toml.load(f)
                
        except ImportError:
            return {"error": "Biblioteca toml não instalada"}
        except Exception as e:
            return {"error": f"Erro ao ler Cargo.toml: {e}"}
            
        # Extrai dependências
        dependencies = {}
        dependencies.update(cargo_data.get("dependencies", {}))
        dependencies.update(cargo_data.get("dev-dependencies", {}))
        
        if not dependencies:
            return {"error": "Nenhuma dependência encontrada"}
            
        # Verifica cada dependência
        results = []
        total_vulnerabilities = 0
        
        for package, version in dependencies.items():
            # Remove versão se for string
            if isinstance(version, str):
                clean_version = version.lstrip("^~")
            else:
                clean_version = "*"
                
            vulns = self._check_osv(package, clean_version, "crates.io")
            if vulns:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": vulns,
                    "count": len(vulns)
                })
                total_vulnerabilities += len(vulns)
            else:
                results.append({
                    "package": package,
                    "version": version,
                    "vulnerabilities": [],
                    "count": 0
                })
                
        return {
            "ecosystem": "Rust",
            "file": str(cargo_toml_path),
            "dependencies_checked": len(dependencies),
            "total_vulnerabilities": total_vulnerabilities,
            "results": results,
            "check_time": datetime.now().isoformat()
        }
        
    def _parse_requirements(self, requirements_path: Path) -> Dict[str, str]:
        """Parse requirements.txt"""
        dependencies = {}
        
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    # Remove comentários
                    if '#' in line:
                        line = line.split('#')[0].strip()
                        
                    # Parse package e versão
                    match = re.match(r'^([a-zA-Z0-9_-]+)([>=<~!]+.*)?$', line)
                    if match:
                        package = match.group(1)
                        version = match.group(2) or "*"
                        dependencies[package] = version
                        
        except Exception as e:
            self.logger.error(f"Erro ao parsear requirements.txt: {e}")
            
        return dependencies
        
    def _parse_go_mod(self, go_mod_path: Path) -> Dict[str, str]:
        """Parse go.mod"""
        dependencies = {}
        
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                in_require = False
                for line in f:
                    line = line.strip()
                    
                    if line.startswith("require"):
                        in_require = True
                        line = line[7:].strip()
                    elif line.startswith(")"):
                        in_require = False
                        continue
                        
                    if in_require or line.startswith("require"):
                        # Parse package e versão
                        parts = line.split()
                        if len(parts) >= 2:
                            package = parts[0]
                            version = parts[1]
                            dependencies[package] = version
                            
        except Exception as e:
            self.logger.error(f"Erro ao parsear go.mod: {e}")
            
        return dependencies
        
    def _check_osv(self, package: str, version: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Verifica vulnerabilidades usando OSV API"""
        
        # Tenta cache primeiro
        cache_key = f"{ecosystem}_{package}_{version}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    if cached_data.get("timestamp"):
                        # Cache válido por 24 horas
                        cache_time = datetime.fromisoformat(cached_data["timestamp"])
                        if (datetime.now() - cache_time).total_seconds() < 86400:
                            return cached_data.get("vulnerabilities", [])
            except Exception as e:
                self.logger.warning(f"Erro ao ler cache: {e}")
                
        # Consulta OSV API
        try:
            payload = {
                "package": {
                    "name": package,
                    "ecosystem": ecosystem
                },
                "version": version
            }
            
            response = requests.post(
                f"{self.osv_api_url}/query",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                vulns = data.get("vulns", [])
                
                # Salva no cache
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "timestamp": datetime.now().isoformat(),
                            "vulnerabilities": vulns
                        }, f, indent=2)
                except Exception as e:
                    self.logger.warning(f"Erro ao salvar cache: {e}")
                    
                return vulns
            else:
                self.logger.warning(f"OSV API retornou status {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao consultar OSV API: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro inesperado ao consultar OSV: {e}")
            return []
            
    def check_directory(self, directory: str) -> Dict[str, Any]:
        """Verifica dependências em um diretório automaticamente"""
        directory = Path(directory)
        
        if not directory.exists():
            return {"error": f"Diretório {directory} não encontrado"}
            
        results = []
        
        # Procura requirements.txt
        requirements_files = list(directory.rglob("requirements.txt"))
        for req_file in requirements_files:
            result = self.check_python(str(req_file))
            if "error" not in result:
                results.append(result)
                
        # Procura package.json
        package_files = list(directory.rglob("package.json"))
        for pkg_file in package_files:
            result = self.check_javascript(str(pkg_file))
            if "error" not in result:
                results.append(result)
                
        # Procura go.mod
        go_mod_files = list(directory.rglob("go.mod"))
        for go_mod in go_mod_files:
            result = self.check_go(str(go_mod))
            if "error" not in result:
                results.append(result)
                
        # Procura Cargo.toml
        cargo_files = list(directory.rglob("Cargo.toml"))
        for cargo in cargo_files:
            result = self.check_rust(str(cargo))
            if "error" not in result:
                results.append(result)
                
        if not results:
            return {"error": "Nenhum arquivo de dependências encontrado"}
            
        total_vulnerabilities = sum(r["total_vulnerabilities"] for r in results)
        
        return {
            "directory": str(directory),
            "files_checked": len(results),
            "total_vulnerabilities": total_vulnerabilities,
            "results": results,
            "check_time": datetime.now().isoformat()
        }