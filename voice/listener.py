#!/usr/bin/env python3
"""
Gênesis Córtex - Voice Listener
Captura de voz usando Vosk STT
"""

import logging
import queue
import threading
import time
from typing import Dict, Any, Optional, Callable
import wave
import json
from pathlib import Path


class VoiceListener:
    """Listener de voz usando Vosk"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.voice_config = config.get("voice", {})
        self.enabled = self.voice_config.get("enabled", False)
        self.stt_config = self.voice_config.get("stt", {})
        
        self.model_path = None
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.listening_thread = None
        
    async def initialize(self):
        """Inicializa o listener de voz"""
        if not self.enabled:
            self.logger.info("Voice listener desabilitado na configuração")
            return
            
        try:
            from vosk import Model, KaldiRecognizer
            
            model_name = self.stt_config.get("model", "pt-BR")
            model_dir = Path("models") / model_name
            
            if not model_dir.exists():
                self.logger.warning(f"Modelo Vosk não encontrado em {model_dir}")
                self.logger.info("Voice listener disponível em modo texto (fallback)")
                return
                
            self.model = Model(str(model_dir))
            sample_rate = self.stt_config.get("sample_rate", 16000)
            self.recognizer = KaldiRecognizer(self.model, sample_rate)
            
            self.logger.info(f"Modelo Vosk carregado: {model_name}")
            
        except ImportError:
            self.logger.warning("Vosk não instalado, voice listener indisponível")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar voice listener: {e}")
            
    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Inicia escuta contínua"""
        if not self.enabled or not self.model:
            self.logger.warning("Voice listener não disponível")
            return False
            
        self.is_listening = True
        self.callback = callback
        
        self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listening_thread.start()
        
        self.logger.info("Voice listener iniciado")
        return True
        
    def stop_listening(self):
        """Para escuta contínua"""
        self.is_listening = False
        if self.listening_thread:
            self.listening_thread.join(timeout=2)
        self.logger.info("Voice listener parado")
        
    def _listen_loop(self):
        """Loop de escuta em thread separada"""
        import pyaudio
        
        try:
            p = pyaudio.PyAudio()
            sample_rate = self.stt_config.get("sample_rate", 16000)
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            self.logger.info("Stream de áudio iniciado")
            
            while self.is_listening:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()
                        
                        if text and self.callback:
                            self.callback(text)
                            
                except Exception as e:
                    self.logger.error(f"Erro no loop de escuta: {e}")
                    break
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar stream de áudio: {e}")
            
    def process_audio_file(self, file_path: str) -> Optional[str]:
        """Processa arquivo de áudio e retorna texto"""
        if not self.model:
            self.logger.warning("Modelo Vosk não disponível")
            return None
            
        try:
            wf = wave.open(file_path, "rb")
            
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != self.stt_config.get("sample_rate", 16000):
                self.logger.error("Formato de áudio não suportado")
                return None
                
            rec = KaldiRecognizer(self.model, wf.getframerate())
            
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        return text
                        
            result = json.loads(rec.FinalResult())
            return result.get("text", "").strip()
            
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo de áudio: {e}")
            return None
            
    def process_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        """Processa chunk de áudio e retorna texto parcial"""
        if not self.recognizer:
            return None
            
        try:
            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                return result.get("text", "").strip()
            else:
                result = json.loads(self.recognizer.PartialResult())
                return result.get("partial", "").strip()
        except Exception as e:
            self.logger.error(f"Erro ao processar chunk de áudio: {e}")
            return None
            
    async def listen_once(self, timeout: int = 5) -> Optional[str]:
        """Escuta uma vez e retorna texto"""
        if not self.enabled or not self.model:
            return None
            
        try:
            import pyaudio
            
            p = pyaudio.PyAudio()
            sample_rate = self.stt_config.get("sample_rate", 16000)
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            frames = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Detecção de silêncio para parar automaticamente
                    if self._detect_silence(data):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Erro ao capturar áudio: {e}")
                    break
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Processa frames coletados
            audio_data = b''.join(frames)
            return self.process_audio_chunk(audio_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao escitar uma vez: {e}")
            return None
            
    def _detect_silence(self, audio_data: bytes, threshold: int = 500) -> bool:
        """Detecta silêncio no áudio"""
        import array
        audio_array = array.array('h', audio_data)
        avg_volume = sum(abs(x) for x in audio_array) / len(audio_array)
        return avg_volume < threshold
        
    def cleanup(self):
        """Limpa recursos"""
        self.stop_listening()
        self.logger.info("Voice listener finalizado")