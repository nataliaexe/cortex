#!/usr/bin/env python3
"""
Gênesis Córtex - Local LLM
Cliente Ollama para DeepSeek-R1
"""

import logging
import aiohttp
import json
from typing import Dict, Any, Optional


class LocalLLM:
    """Cliente para LLM local via Ollama"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.llm_config = config.get("llm", {})
        self.enabled = self.llm_config.get("enabled", False)
        self.api_url = self.llm_config.get("api_url", "http://localhost:11434")
        self.model = self.llm_config.get("model", "deepseek-r1:7b")
        self.timeout = self.llm_config.get("timeout", 60)
        self.generation_config = self.llm_config.get("generation", {})
        
    async def initialize(self):
        """Inicializa o cliente LLM"""
        if not self.enabled:
            self.logger.info("LLM desabilitado na configuração")
            return
            
        try:
            # Verifica se Ollama está rodando
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        self.logger.info("Ollama está rodando e acessível")
                    else:
                        self.logger.warning("Ollama não respondeu corretamente")
                        self.enabled = False
        except Exception as e:
            self.logger.error(f"Erro ao conectar com Ollama: {e}")
            self.enabled = False
            
    async def generate_response(self, user_input: str, context: Dict[str, Any]) -> str:
        """Gera resposta usando o LLM local"""
        
        if not self.enabled:
            return self._fallback_response(user_input)
            
        try:
            # Constrói prompt com contexto
            prompt = self._build_prompt(user_input, context)
            
            # Faz requisição para Ollama
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.generation_config.get("temperature", 0.7),
                        "top_p": self.generation_config.get("top_p", 0.9),
                        "num_predict": self.generation_config.get("max_tokens", 500)
                    }
                }
                
                async with session.post(
                    f"{self.api_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        # Remove bloco de thinking do DeepSeek
                        response_text = self._strip_deepseek_thinking(response_text)
                        return response_text
                    else:
                        self.logger.error(f"Erro na API Ollama: {response.status}")
                        return self._fallback_response(user_input)
                        
        except asyncio.TimeoutError:
            self.logger.error("Timeout na requisição Ollama")
            return self._fallback_response(user_input)
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta: {e}")
            return self._fallback_response(user_input)
            
    def _build_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Constrói prompt com contexto do sistema"""
        
        system_prompt = """Você é o Córtex, um assistente pessoal IA offline especializado em:
- Desenvolvimento de software (Python, JavaScript, Java, C, Assembly, Go, Rust, Kernel Linux)
- Cybersecurity (análise de vulnerabilidades, varredura de portas, análise de binários)
- Robótica com lixo eletrônico
- Neurociência (neuroanatomia funcional, farmacologia, EEG)
- Assistência pessoal (notas, automação, tarefas do sistema)

Responda de forma direta, concisa e útil. Seja técnico quando apropriado."""
        
        context_str = ""
        if context:
            context_items = []
            for key, value in context.items():
                context_items.append(f"{key}: {value}")
            context_str = "\nContexto atual:\n" + "\n".join(context_items)
            
        return f"{system_prompt}\n\n{context_str}\n\nUsuário: {user_input}\n\nAssistente:"
        
    def _strip_deepseek_thinking(self, text: str) -> str:
        """Remove bloco de thinking do DeepSeek"""
        # Remove padrão <|thinking|>...</|thinking|>
        import re
        pattern = r'<\|thinking\|>.*?<\|/thinking\|>'
        cleaned = re.sub(pattern, '', text, flags=re.DOTALL)
        return cleaned.strip()
        
    def _fallback_response(self, user_input: str) -> str:
        """Resposta de fallback quando LLM não está disponível"""
        return f"Entendi sua pergunta sobre '{user_input}', mas o LLM local não está disponível. Tente perguntas mais específicas que possam ser respondidas pelo motor de regras."
        
    async def cleanup(self):
        """Limpa recursos"""
        self.logger.info("LLM client finalizado")