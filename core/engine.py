#!/usr/bin/env python3
"""
Gênesis Córtex - Core Engine
Orquestrador principal do sistema
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .config_loader import ConfigLoader
from .semantic_matcher import SemanticMatcher
from .local_llm import LocalLLM
from .task_executor import TaskExecutor
from .decision_protocol import DecisionProtocol
from .situational_awareness import SituationalAwareness
from .secure_storage import SecureStorage
from .system_actions import SystemActions
from .knowledge_base import LocalKnowledgeBase


class CortexEngine:
    """Motor principal do assistente Córtex"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = ConfigLoader(config_path).load()
        
        # Inicializar componentes
        self.semantic_matcher = SemanticMatcher(self.config)
        self.local_llm = LocalLLM(self.config)
        self.task_executor = TaskExecutor(self.config)
        self.decision_protocol = DecisionProtocol(self.config)
        self.situational_awareness = SituationalAwareness(self.config)
        self.secure_storage = SecureStorage(self.config)
        self.system_actions = SystemActions(self.config)
        self.knowledge_base = LocalKnowledgeBase(self.config)
        
        self.running = False
        
    async def initialize(self):
        """Inicializa todos os componentes"""
        self.logger.info("Inicializando Cortex Engine...")
        
        await self.semantic_matcher.initialize()
        await self.local_llm.initialize()
        await self.task_executor.initialize()
        await self.situational_awareness.initialize()
        
        self.logger.info("Cortex Engine inicializado com sucesso")
        
    async def process_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Processa entrada do usuário e retorna resposta"""

        # 1. Análise situacional
        context = context or {}
        context.update(await self.situational_awareness.analyze_context(user_input))
        # Retrieved local facts are supplied to the LLM, never sent to a remote service.
        context["knowledge_matches"] = self.knowledge_base.search(user_input, limit=3)

        # 2. Matching semântico
        semantic_result = await self.semantic_matcher.match(user_input)

        # 3. Protocolo de decisão (agora usando DecisionProtocol)
        decision = await self.decision_protocol.decide(semantic_result, context)

        if decision == "rules":
            # Resposta do motor de regras
            response = await self.task_executor.execute_intent(
                semantic_result.intent,
                semantic_result.parameters,
                context
            )
        else:
            # Fallback para LLM
            # Route model selection before generation; this does not grant tools.
            context["model_profile"] = self.local_llm.router.select(user_input, context).profile
            response = await self.local_llm.generate_response(user_input, context)

        # 4. Armazenar interação
        await self.secure_storage.store_interaction(user_input, response, context)

        return response
    
    async def start(self):
        """Inicia o motor principal"""
        await self.initialize()
        self.running = True
        self.logger.info("Cortex Engine iniciado")
        
    async def stop(self):
        """Para o motor principal"""
        self.running = False
        await self.local_llm.cleanup()
        await self.task_executor.cleanup()
        self.logger.info("Cortex Engine parado")
        
    async def run_interactive(self):
        """Modo interativo de linha de comando"""
        await self.start()
        
        print("=== Gênesis Córtex ===")
        print("Digite 'sair' para encerrar\n")
        
        try:
            while self.running:
                user_input = input("Você: ")
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    break
                    
                response = await self.process_input(user_input)
                print(f"Córtex: {response}\n")
                
        except KeyboardInterrupt:
            self.logger.info("Interrupção pelo usuário")
        finally:
            await self.stop()


def main():
    """Ponto de entrada principal"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    
    engine = CortexEngine(config_path)
    asyncio.run(engine.run_interactive())


if __name__ == "__main__":
    main()
