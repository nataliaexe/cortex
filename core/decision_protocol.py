#!/usr/bin/env python3
"""
Gênesis Córtex - Decision Protocol
Protocolo de decisão 50/50 para escolha entre motor de regras e LLM
"""

import logging
from typing import Dict, Any


class DecisionProtocol:
    """Protocolo de decisão híbrido"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.rule_threshold = 0.65  # Threshold para usar motor de regras
        self.llm_threshold = 0.35   # Threshold mínimo para usar LLM
        
    async def decide(self, semantic_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Decide qual abordagem usar"""
        
        confidence = semantic_result.get("confidence", 0.0)
        intent = semantic_result.get("intent", "unknown")
        
        # Alta confiança no matching semântico -> motor de regras
        if confidence >= self.rule_threshold:
            self.logger.debug(f"Usando motor de regras (confiança: {confidence:.2f})")
            return "rules"
            
        # Confiança muito baixa -> LLM para tentar entender
        elif confidence <= self.llm_threshold:
            self.logger.debug(f"Usando LLM (confiança: {confidence:.2f})")
            return "llm"
            
        # Zona intermediária -> decisão baseada em contexto
        else:
            return await self._contextual_decision(semantic_result, context)
            
    async def _contextual_decision(self, semantic_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Decisão baseada em contexto"""
        
        intent = semantic_result.get("intent", "unknown")
        
        # Intenções críticas sempre usam motor de regras
        critical_intents = ["shutdown", "reboot", "delete_file", "format_disk"]
        if intent in critical_intents:
            self.logger.debug(f"Intenção crítica, usando motor de regras")
            return "rules"
            
        # Intenções conversacionais preferem LLM
        conversational_intents = ["chat", "explain", "analyze", "opinion"]
        if intent in conversational_intents:
            self.logger.debug(f"Intenção conversacional, usando LLM")
            return "llm"
            
        # Intenções técnicas preferem motor de regras
        technical_intents = ["scan_ports", "analyze_binary", "git_commit", "docker_status"]
        if intent in technical_intents:
            self.logger.debug(f"Intenção técnica, usando motor de regras")
            return "rules"
            
        # Padrão: usa motor de regras para respostas mais rápidas
        self.logger.debug("Decisão padrão: motor de regras")
        return "rules"
        
    async def evaluate_decision(self, approach: str, result: str, user_feedback: Optional[str] = None) -> None:
        """Avalia a decisão tomada para aprendizado futuro"""
        
        if user_feedback:
            self.logger.info(f"Feedback do usuário: {user_feedback}")
            # Aqui poderia implementar aprendizado para ajustar thresholds
        else:
            self.logger.debug(f"Decisão {approach} executada sem feedback")