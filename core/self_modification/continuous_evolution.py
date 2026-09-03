#!/usr/bin/env python3
"""
Gênesis Córtex - Continuous Evolution
Ciclo contínuo de auto-evolução
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json


class ContinuousEvolution:
    """Gerenciador de evolução contínua"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        iteration = config.get("self_modification", {}).get("capability_iteration", {})
        # ``auto_evolution`` is retained only for backwards-compatible configs.
        enabled = iteration.get("enabled", config.get("self_modification", {}).get("auto_evolution", False))
        self.capability_iteration_enabled = enabled
        
        # Componentes
        self.capability_discovery = None
        self.safe_editor = None
        self.sandbox_tester = None
        
        self.is_running = False
        self.evolution_thread = None
        self.evolution_interval = 3600  # 1 hora
        
    async def initialize(self):
        """Inicializa o sistema de evolução"""
        try:
            from .capability_discovery import CapabilityDiscovery
            from .safe_editor import SafeEditor
            from .sandbox_tester import SandboxTester
            
            self.capability_discovery = CapabilityDiscovery(self.config)
            self.safe_editor = SafeEditor(self.config)
            self.sandbox_tester = SandboxTester(self.config)
            
            self.logger.info("Continuous evolution inicializado")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar evolução contínua: {e}")
            
    async def start_evolution(self):
        """Inicia ciclo de evolução"""
        if not self.capability_iteration_enabled:
            self.logger.info("Iteração de capacidade desabilitada")
            return False
            
        self.is_running = True
        self.evolution_thread = asyncio.create_task(self._evolution_loop())
        
        self.logger.info("Ciclo de evolução iniciado")
        return True
        
    async def stop_evolution(self):
        """Para ciclo de evolução"""
        self.is_running = False
        
        if self.evolution_thread:
            self.evolution_thread.cancel()
            try:
                await self.evolution_thread
            except asyncio.CancelledError:
                pass
                
        self.logger.info("Ciclo de evolução parado")
        
    async def _evolution_loop(self):
        """Loop principal de evolução"""
        while self.is_running:
            try:
                self.logger.info("Iniciando ciclo de evolução")
                
                # Descobre lacunas
                gaps = await self.capability_discovery.discover_gaps()
                
                # Gera plano de melhorias
                improvement_plan = await self.capability_discovery.generate_improvement_plan()
                
                # Log do plano
                self.logger.info(f"Plano de melhorias: {len(improvement_plan['priority_high'])} alta prioridade")
                
                # Applies changes only when capability iteration is explicitly enabled.
                if self.capability_iteration_enabled:
                    await self._execute_improvements(improvement_plan)
                else:
                    self.logger.info("Iteração de capacidade desabilitada, apenas análise realizada")
                    
                # Aguarda próximo ciclo
                await asyncio.sleep(self.evolution_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no ciclo de evolução: {e}")
                await asyncio.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
                
    async def _execute_improvements(self, plan: Dict[str, Any]):
        """Executa melhorias automaticamente"""
        for improvement in plan["priority_high"]:
            try:
                self.logger.info(f"Executando melhoria: {improvement['description']}")
                
                # Executa melhoria baseada no tipo
                if improvement["type"] == "missing_module":
                    await self._create_missing_module(improvement)
                elif improvement["type"] == "incomplete_implementation":
                    await self._complete_implementation(improvement)
                elif improvement["type"] == "structure":
                    await self._improve_structure(improvement)
                else:
                    self.logger.warning(f"Tipo de melhoria não implementado: {improvement['type']}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao executar melhoria: {e}")
                
    async def _create_missing_module(self, improvement: Dict[str, Any]):
        """Cria módulo faltante"""
        # Implementação simplificada - na prática seria mais sofisticada
        module_name = improvement["description"].split(":")[-1].strip()
        self.logger.info(f"Criando módulo: {module_name}")
        
        # Aqui seria implementada a lógica de criação de módulos
        # Por segurança, esta é apenas uma implementação placeholder
        
    async def _complete_implementation(self, improvement: Dict[str, Any]):
        """Completa implementação"""
        # Implementação simplificada
        file_info = improvement["description"].split("em ")[-1]
        self.logger.info(f"Completando implementação em: {file_info}")
        
        # Aqui seria implementada a lógica de completar código
        # Por segurança, esta é apenas uma implementação placeholder
        
    async def _improve_structure(self, improvement: Dict[str, Any]):
        """Melhora estrutura do projeto"""
        suggestion = improvement["suggestion"]
        self.logger.info(f"Melhorando estrutura: {suggestion}")
        
        # Implementa sugestão de estrutura
        if "diretório core" in suggestion:
            Path("core").mkdir(exist_ok=True)
        elif "diretório security" in suggestion:
            Path("security").mkdir(exist_ok=True)
            
    async def manual_evolution(self, file_path: str, new_content: str, description: str = "") -> Dict[str, Any]:
        """Executa evolução manual com validação"""
        try:
            # Lê o conteúdo atual do arquivo para verificação
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {
                    "success": False,
                    "message": f"Arquivo {file_path} não existe"
                }

            current_content = file_path_obj.read_text(encoding='utf-8')

            # Testa mudança
            test_results = await self.sandbox_tester.comprehensive_test(file_path, new_content)

            if not test_results["overall_success"]:
                return {
                    "success": False,
                    "message": "Testes falharam",
                    "test_results": test_results
                }

            # Aplica mudança com backup usando o conteúdo atual
            success = await self.safe_editor.edit_file(file_path, current_content, new_content, description)

            if success:
                return {
                    "success": True,
                    "message": "Mudança aplicada com sucesso",
                    "test_results": test_results
                }
            else:
                return {
                    "success": False,
                    "message": "Erro ao aplicar mudança",
                    "test_results": test_results
                }

        except Exception as e:
            self.logger.error(f"Erro na evolução manual: {e}")
            return {
                "success": False,
                "message": f"Erro: {str(e)}"
            }
            
    async def get_evolution_status(self) -> Dict[str, Any]:
        """Retorna status da evolução"""
        gaps = await self.capability_discovery.discover_gaps() if self.capability_discovery else {}
        
        return {
            "is_running": self.is_running,
            "capability_iteration_enabled": self.capability_iteration_enabled,
            "current_gaps": gaps,
            "last_evolution": datetime.now().isoformat() if self.is_running else None
        }
        
    async def set_evolution_interval(self, seconds: int):
        """Define intervalo de evolução"""
        self.evolution_interval = max(60, seconds)  # Mínimo 1 minuto
        self.logger.info(f"Intervalo de evolução definido para {self.evolution_interval} segundos")
        
    async def enable_capability_iteration(self):
        """Enables capability iteration for the current process only."""
        self.capability_iteration_enabled = True
        self.logger.info("Iteração de capacidade habilitada")
        
    async def disable_capability_iteration(self):
        """Disables capability iteration for the current process only."""
        self.capability_iteration_enabled = False
        self.logger.info("Iteração de capacidade desabilitada")
        
    async def cleanup(self):
        """Limpa recursos"""
        await self.stop_evolution()
        
        if self.sandbox_tester:
            await self.sandbox_tester.cleanup()
            
        self.logger.info("Continuous evolution finalizado")
