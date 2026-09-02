#!/usr/bin/env python3
"""
Gênesis Córtex - Background Voice Service
Serviço de voz em background (system tray)
"""

import logging
import asyncio
import threading
from typing import Dict, Any, Optional
from pathlib import Path
import sys


class BackgroundVoiceService:
    """Serviço de voz em background"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.running = False
        self.main_thread = None
        
        # Componentes de voz
        self.listener = None
        self.speaker = None
        self.wake_word_detector = None
        self.conversation = None
        
    async def initialize(self):
        """Inicializa o serviço de voz"""
        try:
            from .listener import VoiceListener
            from .speaker import VoiceSpeaker
            from .wake_word import WakeWordDetector
            from .conversation import VoiceConversation
            
            self.listener = VoiceListener(self.config)
            self.speaker = VoiceSpeaker(self.config)
            self.wake_word_detector = WakeWordDetector(self.config)
            self.conversation = VoiceConversation(
                self.config,
                self.listener,
                self.speaker,
                self.wake_word_detector
            )
            
            await self.conversation.initialize()
            
            self.logger.info("Background voice service inicializado")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar serviço de voz: {e}")
            
    async def start(self):
        """Inicia o serviço em background"""
        self.running = True
        
        # Inicia em thread separada para não bloquear
        self.main_thread = threading.Thread(target=self._run_service, daemon=True)
        self.main_thread.start()
        
        self.logger.info("Background voice service iniciado")
        
    def _run_service(self):
        """Executa o serviço em thread separada"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._service_loop())
        except Exception as e:
            self.logger.error(f"Erro no serviço de voz: {e}")
        finally:
            loop.close()
            
    async def _service_loop(self):
        """Loop principal do serviço"""
        try:
            # Callback de resposta (simulado - seria conectado ao motor principal)
            def response_callback(user_input: str) -> str:
                self.logger.info(f"Processando input: {user_input}")
                # Aqui seria conectado ao motor principal
                return f"Entendi: {user_input}"
                
            await self.conversation.start_conversation(response_callback)
            
        except Exception as e:
            self.logger.error(f"Erro no loop do serviço: {e}")
            
    async def stop(self):
        """Para o serviço"""
        self.running = False
        
        if self.conversation:
            await self.conversation.stop_conversation()
            
        if self.main_thread:
            self.main_thread.join(timeout=2)
            
        self.logger.info("Background voice service parado")
        
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do serviço"""
        if self.conversation:
            return self.conversation.get_status()
        return {"running": self.running}
        
    def cleanup(self):
        """Limpa recursos"""
        if self.conversation:
            self.conversation.cleanup()
        self.logger.info("Background voice service finalizado")


def run_background_service(config_path: str = "config.yaml"):
    """Executa o serviço de voz em background"""
    import yaml
    
    # Carrega configuração
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Erro ao carregar configuração: {e}")
        sys.exit(1)
        
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Cria e inicia serviço
    service = BackgroundVoiceService(config)
    
    async def main():
        await service.initialize()
        await service.start()
        
        try:
            # Mantém serviço rodando
            while service.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário")
        finally:
            await service.stop()
            service.cleanup()
            
    asyncio.run(main())


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    run_background_service(config_file)