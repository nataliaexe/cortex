#!/usr/bin/env python3
"""
Gênesis Córtex - Sistema de Voz Avançado
Integração Piper TTS + Coqui XTTS para clonagem de voz
"""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import json

try:
    import torch
    import numpy as np
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False


class VoiceEngine(Enum):
    """Motores de voz disponíveis"""
    PIPER = "piper"
    COQUI_XTTS = "coqui_xtts"


class VoiceProfile(Enum):
    """Perfis de voz pré-configurados"""
    CASUAL = "casual"
    TECHNICAL = "technical"
    ALERT = "alert"
    FUN = "fun"


class AdvancedVoiceSystem:
    """Sistema de voz avançado com Piper TTS e clonagem"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.voice_config = config.get("voice", {})
        
        # Configurações padrão
        self.engine = VoiceEngine(self.voice_config.get("engine", "piper"))
        self.piper_voice = self.voice_config.get("piper_voice", "luciana")
        self.cloned_voice = self.voice_config.get("cloned_voice", "")
        self.speed = self.voice_config.get("speed", 1.0)
        self.pitch = self.voice_config.get("pitch", 0)
        self.volume = self.voice_config.get("volume", 0.7)
        self.profile = VoiceProfile(self.voice_config.get("profile", "casual"))
        
        # Diretórios
        self.voices_dir = Path("vozes")
        self.models_dir = Path("voice/models")
        self.voices_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado do TTS
        self.tts_model = None
        self.piper_model = None
        
        # Perfis de contexto
        self.profiles_config = {
            VoiceProfile.CASUAL: {
                "engine": VoiceEngine.PIPER,
                "voice": "luciana",
                "speed": 1.0,
                "pitch": 0,
                "volume": 0.7
            },
            VoiceProfile.TECHNICAL: {
                "engine": VoiceEngine.PIPER,
                "voice": "faber",
                "speed": 0.95,
                "pitch": -0.1,
                "volume": 0.8
            },
            VoiceProfile.ALERT: {
                "engine": VoiceEngine.PIPER,
                "voice": "faber",
                "speed": 0.9,
                "pitch": -0.2,
                "volume": 1.0
            },
            VoiceProfile.FUN: {
                "engine": VoiceEngine.COQUI_XTTS,
                "voice": "rick_sanchez",
                "speed": 1.1,
                "pitch": 0.2,
                "volume": 0.8
            }
        }
        
        # URLs para download de vozes Piper
        self.piper_voices = {
            "luciana": {
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/luciana/medium/pt_BR-luciana-medium.onnx",
                "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/luciana/medium/pt_BR-luciana-medium.onnx.json"
            },
            "faber": {
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
                "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"
            }
        }
        
    async def initialize(self) -> bool:
        """Inicializa o sistema de voz"""
        self.logger.info("Inicializando sistema de voz avançado")
        
        try:
            # Carregar vozes Piper se necessário
            if self.engine == VoiceEngine.PIPER:
                await self._load_piper_model()
            
            # Carregar modelo Coqui se necessário
            if self.engine == VoiceEngine.COQUI_XTTS and COQUI_AVAILABLE:
                await self._load_coqui_model()
            
            self.logger.info(f"Sistema de voz inicializado com engine: {self.engine.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistema de voz: {e}")
            return False
    
    async def _load_piper_model(self) -> None:
        """Carrega modelo Piper TTS"""
        voice_key = self.piper_voice
        if voice_key not in self.piper_voices:
            self.logger.warning(f"Voz Piper '{voice_key}' não encontrada, usando fallback")
            voice_key = "luciana"
        
        voice_info = self.piper_voices[voice_key]
        model_path = self.models_dir / f"pt_BR-{voice_key}-medium.onnx"
        config_path = self.models_dir / f"pt_BR-{voice_key}-medium.onnx.json"
        
        # Baixar se não existir
        if not model_path.exists():
            await self._download_piper_voice(voice_key, voice_info)
        
        # Carregar modelo (simulado - na prática usaria piper-tts)
        self.piper_model = {
            "path": str(model_path),
            "config": str(config_path),
            "voice": voice_key
        }
        
        self.logger.info(f"Modelo Piper carregado: {voice_key}")
    
    async def _download_piper_voice(self, voice_key: str, voice_info: Dict[str, str]) -> None:
        """Baixa voz Piper do HuggingFace"""
        self.logger.info(f"Baixando voz Piper: {voice_key}")
        
        try:
            import requests
            
            # Baixar modelo
            model_response = requests.get(voice_info["url"], timeout=300)
            model_path = self.models_dir / f"pt_BR-{voice_key}-medium.onnx"
            model_path.write_bytes(model_response.content)
            
            # Baixar config
            config_response = requests.get(voice_info["config"], timeout=60)
            config_path = self.models_dir / f"pt_BR-{voice_key}-medium.onnx.json"
            config_path.write_bytes(config_response.content)
            
            self.logger.info(f"Voz Piper baixada com sucesso: {voice_key}")
            
        except Exception as e:
            self.logger.error(f"Erro ao baixar voz Piper: {e}")
            raise
    
    async def _load_coqui_model(self) -> None:
        """Carrega modelo Coqui XTTS para clonagem"""
        if not COQUI_AVAILABLE:
            self.logger.warning("Coqui XTTS não disponível, usando fallback")
            self.engine = VoiceEngine.PIPER
            await self._load_piper_model()
            return
        
        try:
            # Carregar modelo XTTS
            self.tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            self.tts_model.to("cpu")
            
            self.logger.info("Modelo Coqui XTTS carregado")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo Coqui: {e}")
            self.engine = VoiceEngine.PIPER
            await self._load_piper_model()
    
    async def speak(self, text: str, profile: Optional[VoiceProfile] = None) -> bool:
        """Sintetiza e reproduz texto como voz"""
        if not text:
            return False
        
        # Usar perfil específico se fornecido
        if profile:
            await self._apply_profile(profile)
        
        try:
            if self.engine == VoiceEngine.PIPER:
                return await self._speak_piper(text)
            elif self.engine == VoiceEngine.COQUI_XTTS:
                return await self._speak_coqui(text)
            else:
                return await self._speak_piper(text)
                
        except Exception as e:
            self.logger.error(f"Erro ao sintetizar voz: {e}")
            return False
    
    async def _speak_piper(self, text: str) -> bool:
        """Sintetiza voz usando Piper TTS"""
        try:
            # Preparar comando Piper (simulado - na prática usaria piper-tts)
            # Aqui usamos uma implementação simplificada com espeak/festival como fallback
            
            # Normalizar texto
            text = self._normalize_text(text)
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Executar síntese (simulado - usar piper real na produção)
            try:
                # Tentar usar piper se disponível
                result = subprocess.run([
                    "piper",
                    "--model", self.piper_model["path"],
                    "--output_file", temp_path
                ], input=text.encode(), capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    return await self._play_audio(temp_path)
                else:
                    # Fallback para espeak
                    return await self._speak_espeak(text)
                    
            except FileNotFoundError:
                # Fallback para espeak
                return await self._speak_espeak(text)
                
        except Exception as e:
            self.logger.error(f"Erro na síntese Piper: {e}")
            return False
    
    async def _speak_espeak(self, text: str) -> bool:
        """Sintetiza voz usando espeak como fallback"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            result = subprocess.run([
                "espeak",
                "-v", "pt",
                "-s", str(int(self.speed * 150)),
                "-p", str(int(self.pitch * 50)),
                "-a", str(int(self.volume * 100)),
                "-w", temp_path,
                text
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0:
                return await self._play_audio(temp_path)
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na síntese espeak: {e}")
            return False
    
    async def _speak_coqui(self, text: str) -> bool:
        """Sintetiza voz usando Coqui XTTS com clonagem"""
        if not COQUI_AVAILABLE or not self.tts_model:
            return await self._speak_piper(text)
        
        try:
            # Verificar se há voz clonada
            if self.cloned_voice:
                voice_file = self.voices_dir / f"{self.cloned_voice}.wav"
                if voice_file.exists():
                    # Sintetizar com voz clonada
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    self.tts_model.tts_to_file(
                        text=text,
                        speaker_wav=str(voice_file),
                        language="pt",
                        file_path=temp_path
                    )
                    
                    return await self._play_audio(temp_path)
            
            # Fallback para voz padrão
            return await self._speak_piper(text)
            
        except Exception as e:
            self.logger.error(f"Erro na síntese Coqui: {e}")
            return await self._speak_piper(text)
    
    async def _play_audio(self, audio_path: str) -> bool:
        """Reproduz arquivo de áudio"""
        try:
            # Ajustar volume
            if self.volume != 1.0:
                await self._adjust_volume(audio_path, self.volume)
            
            # Reproduzir usando player do sistema
            subprocess.run([
                "aplay",  # Linux
                audio_path
            ], capture_output=True, timeout=60)
            
            # Limpar arquivo temporário
            Path(audio_path).unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao reproduzir áudio: {e}")
            Path(audio_path).unlink(missing_ok=True)
            return False
    
    async def _adjust_volume(self, audio_path: str, volume: float) -> None:
        """Ajusta volume do arquivo de áudio"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Usar ffmpeg para ajustar volume
            subprocess.run([
                "ffmpeg",
                "-i", audio_path,
                "-filter:a", f"volume={volume}",
                "-y",  # Sobrescrever
                temp_path
            ], capture_output=True, timeout=30)
            
            # Substituir original
            Path(temp_path).replace(audio_path)
            
        except Exception as e:
            self.logger.warning(f"Não foi possível ajustar volume: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para síntese"""
        # Remover caracteres problemáticos
        text = text.replace("...", ".")
        text = text.replace("!!", "!")
        text = text.replace("??", "?")
        
        # Limitar comprimento
        if len(text) > 500:
            text = text[:500] + "..."
        
        return text.strip()
    
    async def _apply_profile(self, profile: VoiceProfile) -> None:
        """Aplica perfil de voz"""
        if profile not in self.profiles_config:
            self.logger.warning(f"Perfil {profile} não encontrado")
            return
        
        profile_config = self.profiles_config[profile]
        
        self.engine = profile_config["engine"]
        self.piper_voice = profile_config["voice"]
        self.speed = profile_config["speed"]
        self.pitch = profile_config["pitch"]
        self.volume = profile_config["volume"]
        
        # Recarregar modelo se necessário
        if self.engine == VoiceEngine.PIPER:
            await self._load_piper_model()
        elif self.engine == VoiceEngine.COQUI_XTTS:
            await self._load_coqui_model()
    
    async def set_profile(self, profile: VoiceProfile) -> None:
        """Define perfil de voz"""
        await self._apply_profile(profile)
        self.profile = profile
        self.logger.info(f"Perfil de voz alterado para: {profile.value}")
    
    async def download_all_piper_voices(self) -> Dict[str, bool]:
        """Baixa todas as vozes Piper disponíveis"""
        results = {}
        
        for voice_key, voice_info in self.piper_voices.items():
            try:
                await self._download_piper_voice(voice_key, voice_info)
                results[voice_key] = True
            except Exception as e:
                self.logger.error(f"Erro ao baixar voz {voice_key}: {e}")
                results[voice_key] = False
        
        return results
    
    async def clone_voice(self, voice_file: str, voice_name: str) -> bool:
        """Clona voz a partir de arquivo de áudio"""
        if not COQUI_AVAILABLE:
            self.logger.warning("Coqui XTTS não disponível para clonagem")
            return False
        
        try:
            # Copiar arquivo para diretório de vozes
            source_path = Path(voice_file)
            dest_path = self.voices_dir / f"{voice_name}.wav"
            
            if not source_path.exists():
                self.logger.error(f"Arquivo de voz não encontrado: {voice_file}")
                return False
            
            # Converter para WAV se necessário
            if source_path.suffix != ".wav":
                await self._convert_to_wav(source_path, dest_path)
            else:
                import shutil
                shutil.copy(source_path, dest_path)
            
            self.cloned_voice = voice_name
            self.logger.info(f"Voz clonada com sucesso: {sample_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao clonar voz: {e}")
            return False
    
    async def _convert_to_wav(self, source_path: Path, dest_path: Path) -> None:
        """Converte arquivo de áudio para WAV"""
        subprocess.run([
            "ffmpeg",
            "-i", str(source_path),
            "-ar", "16000",  # Sample rate para XTTS
            "-ac", "1",      # Mono
            "-y",
            str(dest_path)
        ], capture_output=True, timeout=60)
    
    async def test_voice(self, text: str = "Olá! Este é um teste de voz do Córtex.") -> bool:
        """Testa o sistema de voz"""
        self.logger.info("Testando sistema de voz")
        return await self.speak(text)
    
    async def switch_to_rick_mode(self) -> None:
        """Ativa modo Rick Sanchez"""
        await self.set_profile(VoiceProfile.FUN)
        await self.speak("Wubba lubba dub dub!")
    
    async def switch_to_normal_mode(self) -> None:
        """Volta para modo normal"""
        await self.set_profile(VoiceProfile.CASUAL)
        await self.speak("Modo normal ativado")
    
    def get_available_voices(self) -> List[str]:
        """Retorna lista de vozes disponíveis"""
        voices = list(self.piper_voices.keys())
        
        # Adicionar vozes clonadas
        if self.voices_dir.exists():
            cloned_voices = [f.stem for f in self.voices_dir.glob("*.wav")]
            voices.extend(cloned_voices)
        
        return voices
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do sistema de voz"""
        return {
            "engine": self.engine.value,
            "piper_voice": self.piper_voice,
            "cloned_voice": self.cloned_voice,
            "speed": self.speed,
            "pitch": self.pitch,
            "volume": self.volume,
            "profile": self.profile.value,
            "piper_available": True,
            "coqui_available": COQUI_AVAILABLE,
            "available_voices": self.get_available_voices()
        }