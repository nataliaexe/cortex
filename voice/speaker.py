#!/usr/bin/env python3
"""
Gênesis Córtex - Voice Speaker
Síntese de voz usando Piper TTS
"""

import logging
import subprocess
import tempfile
import platform
from typing import Dict, Any, Optional
from pathlib import Path


class VoiceSpeaker:
    """Speaker de voz usando Piper TTS"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.voice_config = config.get("voice", {})
        self.enabled = self.voice_config.get("enabled", False)
        self.tts_config = self.voice_config.get("tts", {})
        
        self.current_voice = self.tts_config.get("voice", "luciana")
        self.voice_profile = None
        self.piper_available = False
        
    async def initialize(self):
        """Inicializa o speaker de voz"""
        if not self.enabled:
            self.logger.info("Voice speaker desabilitado na configuração")
            return
            
        try:
            # Verifica se piper está disponível
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.piper_available = True
                self.logger.info("Piper TTS disponível")
                await self.load_voice_profile(self.current_voice)
            else:
                self.logger.warning("Piper TTS não encontrado")
                
        except FileNotFoundError:
            self.logger.warning("Piper TTS não instalado")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar voice speaker: {e}")
            
    async def load_voice_profile(self, voice_name: str) -> bool:
        """Carrega perfil de voz"""
        self.current_voice = voice_name
        voice_path = Path("models/piper") / f"{voice_name}.onnx"
        
        if not voice_path.exists():
            self.logger.warning(f"Perfil de voz {voice_name} não encontrado")
            return False
            
        self.voice_profile = str(voice_path)
        self.logger.info(f"Perfil de voz carregado: {voice_name}")
        return True
        
    async def speak(self, text: str, output_file: Optional[str] = None) -> bool:
        """Sintetiza e reproduz texto"""
        if not self.enabled or not self.piper_available:
            self.logger.warning("Voice speaker não disponível")
            return False
            
        try:
            if output_file:
                return await self.synthesize_to_file(text, output_file)
            else:
                return await self.synthesize_and_play(text)
                
        except Exception as e:
            self.logger.error(f"Erro ao falar: {e}")
            return False
            
    async def synthesize_to_file(self, text: str, output_file: str) -> bool:
        """Sintetiza texto para arquivo de áudio"""
        if not self.voice_profile:
            self.logger.warning("Perfil de voz não carregado")
            return False
            
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                "piper",
                "--model", self.voice_profile,
                "--output_file", str(output_path)
            ]
            
            # Usa stdin para o texto
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=text, timeout=30)
            
            if process.returncode == 0:
                self.logger.info(f"Áudio sintetizado: {output_path}")
                return True
            else:
                self.logger.error(f"Erro no Piper: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout na síntese de voz")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao sintetizar para arquivo: {e}")
            return False
            
    async def synthesize_and_play(self, text: str) -> bool:
        """Sintetiza e reproduz texto"""
        try:
            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Sintetiza
            if not await self.synthesize_to_file(text, temp_path):
                return False
                
            # Reproduz
            if await self.play_audio(temp_path):
                # Remove arquivo temporário
                Path(temp_path).unlink()
                return True
            else:
                Path(temp_path).unlink()
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao sintetizar e reproduzir: {e}")
            return False
            
    async def play_audio(self, audio_file: str) -> bool:
        """Reproduz arquivo de áudio"""
        try:
            if platform.system() == "Linux":
                # Usa aplay (ALSA) ou paplay (PulseAudio)
                for player in ["paplay", "aplay", "mpg123", "ffplay"]:
                    try:
                        result = subprocess.run(
                            [player, audio_file],
                            capture_output=True,
                            timeout=30
                        )
                        if result.returncode == 0:
                            return True
                    except FileNotFoundError:
                        continue
                        
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["afplay", audio_file], timeout=30)
                return True
                
            elif platform.system() == "Windows":
                subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"], timeout=30)
                return True
                
            self.logger.warning("Nenhum player de áudio encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao reproduzir áudio: {e}")
            return False
            
    async def set_voice(self, voice_name: str) -> bool:
        """Define voz atual"""
        return await self.load_voice_profile(voice_name)
        
    async def get_available_voices(self) -> list:
        """Retorna vozes disponíveis"""
        voices_dir = Path("models/piper")
        
        if not voices_dir.exists():
            return []
            
        voices = []
        for voice_file in voices_dir.glob("*.onnx"):
            voices.append(voice_file.stem)
            
        return voices
        
    async def set_speed(self, speed: float) -> bool:
        """Define velocidade da fala (0.5 a 2.0)"""
        # Piper não suporta speed nativamente, seria necessário processamento adicional
        self.logger.info(f"Velocidade definida para {speed} (requer implementação adicional)")
        return True
        
    async def set_pitch(self, pitch: float) -> bool:
        """Define pitch da fala"""
        # Piper não suporta pitch nativamente, seria necessário processamento adicional
        self.logger.info(f"Pitch definido para {pitch} (requer implementação adicional)")
        return True
        
    async def get_voice_info(self) -> Dict[str, Any]:
        """Retorna informações da voz atual"""
        return {
            "current_voice": self.current_voice,
            "voice_profile": self.voice_profile,
            "piper_available": self.piper_available,
            "enabled": self.enabled
        }
        
    def cleanup(self):
        """Limpa recursos"""
        self.logger.info("Voice speaker finalizado")