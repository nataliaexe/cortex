#!/usr/bin/env python3
"""
Gênesis Córtex - Wake Word Detector
Detecção de wake word "Ei Córtex"
"""

import logging
import queue
import threading
import time
import json
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class WakeWordDetector:
    """Detector de wake word"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.voice_config = config.get("voice", {})
        self.enabled = self.voice_config.get("enabled", False) and self.voice_config.get("wake_word", {}).get("enabled", False)
        
        self.wake_word_config = self.voice_config.get("wake_word", {})
        self.phrase = self.wake_word_config.get("phrase", "ei córtex").lower()
        self.sensitivity = self.wake_word_config.get("sensitivity", 0.5)
        
        self.is_detecting = False
        self.detection_thread = None
        self.callback = None
        
        # Para simulação (usará Vosk ou poracora se disponível)
        self.listener = None
        
    async def initialize(self):
        """Inicializa o detector de wake word"""
        if not self.enabled:
            self.logger.info("Wake word detector desabilitado")
            return
            
        try:
            # Tenta usar poracora se disponível
            try:
                import poracora
                self.poracora_available = True
                self.logger.info("Poracora disponível para detecção de wake word")
            except ImportError:
                self.poracora_available = False
                self.logger.info("Poracora não disponível, usando detecção baseada em Vosk")
                
        except Exception as e:
            self.logger.error(f"Erro ao inicializar wake word detector: {e}")
            
    def start_detection(self, callback: Callable[[], None]):
        """Inicia detecção de wake word"""
        if not self.enabled:
            self.logger.warning("Wake word detector não disponível")
            return False
            
        self.is_detecting = True
        self.callback = callback
        
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        
        self.logger.info(f"Detecção de wake word iniciada: '{self.phrase}'")
        return True
        
    def stop_detection(self):
        """Para detecção de wake word"""
        self.is_detecting = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        self.logger.info("Detecção de wake word parada")
        
    def _detection_loop(self):
        """Loop de detecção em thread separada"""
        if self.poracora_available:
            self._poracora_detection_loop()
        else:
            self._vosk_detection_loop()
            
    def _poracora_detection_loop(self):
        """Loop de detecção usando Poracora"""
        try:
            import poracora
            import pyaudio
            
            # Carrega modelo de wake word
            model_path = Path("models/poracora") / self.phrase.replace(" ", "_")
            
            if not model_path.exists():
                self.logger.warning(f"Modelo Poracora não encontrado: {model_path}")
                self._vosk_detection_loop()
                return
                
            poracora_engine = poracora.Poracora(str(model_path))
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            self.logger.info("Stream de áudio iniciado para detecção")
            
            while self.is_detecting:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    
                    if poracora_engine.process_audio(data):
                        self.logger.info(f"Wake word detectada: '{self.phrase}'")
                        if self.callback:
                            self.callback()
                            
                except Exception as e:
                    self.logger.error(f"Erro no loop de detecção: {e}")
                    break
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            self.logger.error(f"Erro na detecção Poracora: {e}")
            self._vosk_detection_loop()
            
    def _vosk_detection_loop(self):
        """Loop de detecção usando Vosk (fallback)"""
        try:
            from vosk import Model, KaldiRecognizer
            import pyaudio
            
            model_path = Path("models") / self.voice_config.get("stt", {}).get("model", "pt-BR")
            
            if not model_path.exists():
                self.logger.warning("Modelo Vosk não encontrado para detecção de wake word")
                time.sleep(1)
                return
                
            model = Model(str(model_path))
            recognizer = KaldiRecognizer(model, 16000)
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            self.logger.info("Stream de áudio iniciado para detecção (Vosk)")
            
            while self.is_detecting:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").lower()
                        
                        if self.phrase in text:
                            self.logger.info(f"Wake word detectada: '{self.phrase}'")
                            if self.callback:
                                self.callback()
                                
                except Exception as e:
                    self.logger.error(f"Erro no loop de detecção: {e}")
                    break
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            self.logger.error(f"Erro na detecção Vosk: {e}")
            
    def set_wake_word(self, phrase: str):
        """Define wake word"""
        self.phrase = phrase.lower()
        self.logger.info(f"Wake word alterada para: '{self.phrase}'")
        
    def set_sensitivity(self, sensitivity: float):
        """Define sensibilidade (0.0 a 1.0)"""
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self.logger.info(f"Sensibilidade definida para: {self.sensitivity}")
        
    def get_info(self) -> Dict[str, Any]:
        """Retorna informações do detector"""
        return {
            "enabled": self.enabled,
            "phrase": self.phrase,
            "sensitivity": self.sensitivity,
            "poracora_available": getattr(self, 'poracora_available', False),
            "is_detecting": self.is_detecting
        }
        
    def cleanup(self):
        """Limpa recursos"""
        self.stop_detection()
        self.logger.info("Wake word detector finalizado")