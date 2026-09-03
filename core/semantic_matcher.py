#!/usr/bin/env python3
"""
Gênesis Córtex - Semantic Matcher
Matching semântico usando Sentence-Transformers
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class SemanticMatcher:
    """Matcher semântico para intenções"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.model = None
        self.intents_db = {}
        self.threshold = 0.65
        self.intent_embeddings_cache = {}  # Cache de embeddings por intent
        
    async def initialize(self):
        """Inicializa o modelo e carrega intenções"""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self.config.get("memory", {}).get("long_term", {}).get(
                "embedding_model", 
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"Modelo de embeddings carregado: {model_name}")
            
            await self._load_intents()
            
        except ImportError:
            self.logger.warning("sentence-transformers não instalado, usando fallback")
            self.model = None
        except Exception as e:
            self.logger.error(f"Erro ao inicializar semantic matcher: {e}")
            self.model = None
            
    async def _load_intents(self):
        """Carrega base de intenções e pré-calcula embeddings"""
        intents_path = Path("personality/base_training.json")
        if intents_path.exists():
            with open(intents_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.intents_db = data.get("intents", {})

            # Pré-calcula embeddings para todos os exemplos de todas as intents
            if self.model:
                self.logger.info("Pré-calculando embeddings para intenções...")
                for intent_name, intent_data in self.intents_db.items():
                    examples = intent_data.get("examples", [])
                    if examples:
                        try:
                            embeddings = self.model.encode(examples)
                            self.intent_embeddings_cache[intent_name] = embeddings
                        except Exception as e:
                            self.logger.warning(f"Erro ao calcular embeddings para intent {intent_name}: {e}")

            self.logger.info(f"{len(self.intents_db)} intenções carregadas")
        else:
            self.logger.warning("Arquivo de intenções não encontrado")
            
    async def match(self, user_input: str) -> Dict[str, Any]:
        """Realiza matching semântico da entrada do usuário"""

        if not self.model:
            return self._fallback_match(user_input)

        try:
            # Calcula embedding apenas para a entrada do usuário
            input_embedding = self.model.encode([user_input])

            best_match = None
            best_score = 0

            for intent_name, intent_data in self.intents_db.items():
                # Usa embeddings cacheados se disponíveis, senão calcula
                if intent_name in self.intent_embeddings_cache:
                    example_embeddings = self.intent_embeddings_cache[intent_name]
                else:
                    examples = intent_data.get("examples", [])
                    if not examples:
                        continue
                    example_embeddings = self.model.encode(examples)
                    # Cacheia para futuras chamadas
                    self.intent_embeddings_cache[intent_name] = example_embeddings

                # Calcula similaridade com exemplos
                similarities = self._cosine_similarity(input_embedding, example_embeddings)
                max_similarity = similarities.max()

                if max_similarity > best_score:
                    best_score = max_similarity
                    best_match = {
                        "intent": intent_name,
                        "confidence": float(max_similarity),
                        "parameters": self._extract_parameters(user_input, intent_data)
                    }

            if best_match and best_match["confidence"] > self.threshold:
                return best_match
            else:
                return {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "parameters": {}
                }

        except Exception as e:
            self.logger.error(f"Erro no matching semântico: {e}")
            return self._fallback_match(user_input)
            
    def _cosine_similarity(self, a, b):
        """Calcula similaridade de cosseno"""
        import numpy as np
        return np.dot(a, b.T) / (np.linalg.norm(a) * np.linalg.norm(b, axis=1))
        
    def _extract_parameters(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """Extrai parâmetros da entrada do usuário"""
        # Implementação simplificada - pode ser expandida com regex ou NLP
        parameters = {}
        
        # Extrai parâmetros definidos na intenção
        for param_name, param_config in intent_data.get("parameters", {}).items():
            param_type = param_config.get("type", "string")
            # Lógica de extração específica por tipo
            if param_type == "number":
                import re
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    parameters[param_name] = int(numbers[0])
            elif param_type == "path":
                import re
                paths = re.findall(r'[\w\-\.\/]+', user_input)
                if paths:
                    parameters[param_name] = paths[0]
            else:
                parameters[param_name] = user_input
                
        return parameters
        
    def _fallback_match(self, user_input: str) -> Dict[str, Any]:
        """Fallback simples baseado em palavras-chave"""
        user_input_lower = user_input.lower()
        
        keyword_map = {
            "ajuda": {"intent": "help", "confidence": 0.8},
            "informação": {"intent": "system_info", "confidence": 0.7},
            "processo": {"intent": "running_processes", "confidence": 0.7},
            "arquivo": {"intent": "list_files", "confidence": 0.6},
            "memória": {"intent": "memory_usage", "confidence": 0.7},
            "rede": {"intent": "network_status", "confidence": 0.7},
            "escanear": {"intent": "scan_ports", "confidence": 0.7},
            "segurança": {"intent": "security_query", "confidence": 0.6},
            "nota": {"intent": "create_note", "confidence": 0.7},
            "timer": {"intent": "set_timer", "confidence": 0.8},
            "backup": {"intent": "create_backup", "confidence": 0.7},
        }
        
        for keyword, match in keyword_map.items():
            if keyword in user_input_lower:
                return match
                
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "parameters": {}
        }