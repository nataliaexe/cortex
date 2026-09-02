#!/usr/bin/env python3
"""
Gênesis Córtex - Voice Conversation
Gerenciador de conversação por voz
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class VoiceConversation:
    """Gerenciador de conversação por voz"""
    
    def __init__(self, config: Dict[str, Any], listener, speaker, wake_word_detector):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.listener = listener
        self.speaker = speaker
        self.wake_word_detector = wake_word_detector
        
        self.is_conversing = False
        self.conversation_active = False
        self.response_callback = None
        
    async def initialize(self):
        """Inicializa o gerenciador de conversação"""
        await self.listener.initialize()
        await self.speaker.initialize()
        await self.wake_word_detector.initialize()
        
        # Configura callback do wake word
        self.wake_word_detector.start_detection(self._on_wake_word)
        
        self.logger.info("Voice conversation manager inicializado")
        
    def _on_wake_word(self):
        """Callback quando wake word é detectada"""
        self.logger.info("Wake word detectada, iniciando conversação")
        self.conversation_active = True
        
    async def start_conversation(self, response_callback: Callable[[str], str]):
        """Inicia modo de conversação"""
        self.response_callback = response_callback
        self.is_conversing = True
        
        self.logger.info("Conversação iniciada")
        
        # Aguarda wake word
        while self.is_conversing:
            if self.conversation_active:
                await self._process_conversation_turn()
                self.conversation_active = False
                
            await asyncio.sleep(0.1)
            
    async def _process_conversation_turn(self):
        """Processa um turno de conversação"""
        try:
            # Fala prompt
            await self.speaker.speak("Estou ouvindo")
            
            # Escuta resposta
            user_input = await self.listener.listen_once(timeout=10)
            
            if user_input:
                self.logger.info(f"Usuário disse: {user_input}")
                
                # Processa resposta
                if self.response_callback:
                    response = self.response_callback(user_input)
                    self.logger.info(f"Respondendo: {response}")
                    
                    # Fala resposta
                    await self.speaker.speak(response)
                else:
                    await self.speaker.speak("Não tenho resposta para isso")
            else:
                await self.speaker.speak("Não entendi")
                
        except Exception as e:
            self.logger.error(f"Erro no turno de conversação: {e}")
            
    async def stop_conversation(self):
        """Para modo de conversação"""
        self.is_conversing = False
        self.conversation_active = False
        self.wake_word_detector.stop_detection()
        
        self.logger.info("Conversação parada")
        
    async def ask_question(self, question: str, timeout: int = 10) -> Optional[str]:
        """Faz uma pergunta e espera resposta"""
        try:
            # Fala pergunta
            await self.speaker.speak(question)
            
            # Escuta resposta
            response = await self.listener.listen_once(timeout=timeout)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erro ao fazer pergunta: {e}")
            return None
            
    async def confirm(self, message: str) -> bool:
        """Pede confirmação ao usuário"""
        try:
            response = await self.ask_question(f"{message}. Responda sim ou não.")
            
            if response:
                response_lower = response.lower()
                return "sim" in response_lower or "yes" in response_lower or "y" in response_lower
                
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao pedir confirmação: {e}")
            return False
            
    async def get_choice(self, message: str, options: list) -> Optional[str]:
        """Pede ao usuário para escolher entre opções"""
        try:
            options_str = ", ".join(options)
            response = await self.ask_question(f"{message}. Opções: {options_str}")
            
            if response:
                response_lower = response.lower()
                for option in options:
                    if option.lower() in response_lower:
                        return option
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter escolha: {e}")
            return None
            
    async def set_voice(self, voice_name: str) -> bool:
        """Define voz do speaker"""
        return await self.speaker.set_voice(voice_name)
        
    async def get_available_voices(self) -> list:
        """Retorna vozes disponíveis"""
        return await self.speaker.get_available_voices()
        
    def get_status(self) -> Dict[str, Any]:
        """Retorna status da conversação"""
        return {
            "is_conversing": self.is_conversing,
            "conversation_active": self.conversation_active,
            "listener_available": self.listener.enabled,
            "speaker_available": self.speaker.enabled,
            "wake_word_available": self.wake_word_detector.enabled
        }
        
    def cleanup(self):
        """Limpa recursos"""
        self.stop_conversation()
        self.listener.cleanup()
        self.speaker.cleanup()
        self.wake_word_detector.cleanup()
        self.logger.info("Voice conversation manager finalizado")