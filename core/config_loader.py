#!/usr/bin/env python3
"""
Gênesis Córtex - Config Loader
Carregador de configuração YAML
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Carrega e gerencia configurações do sistema"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo YAML"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Arquivo de configuração {self.config_path} não encontrado, usando padrões")
                return self._get_default_config()
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
                
            self.logger.info(f"Configuração carregada de {self.config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            return self._get_default_config()
            
    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Salva configuração no arquivo YAML"""
        try:
            config_to_save = config or self.config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"Configuração salva em {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any) -> None:
        """Define valor de configuração"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "system": {
                "name": "Gênesis Córtex",
                "version": "1.0.0",
                "log_level": "INFO",
                "data_dir": "data",
                "log_dir": "logs"
            },
            "llm": {
                "enabled": True,
                "provider": "ollama",
                "model": "deepseek-r1:7b",
                "models": {
                    "reasoning": "deepseek-r1:7b",
                    "coding": "qwen2.5-coder:7b"
                },
                "api_url": "http://localhost:11434",
                "timeout": 60,
                "generation": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            },
            "voice": {
                "enabled": False,
                "stt": {
                    "provider": "vosk",
                    "model": "pt-BR",
                    "sample_rate": 16000
                },
                "tts": {
                    "provider": "piper",
                    "voice": "luciana",
                    "sample_rate": 22050
                },
                "wake_word": {
                    "enabled": False,
                    "phrase": "ei córtex",
                    "sensitivity": 0.5
                }
            },
            "memory": {
                "short_term": {
                    "type": "sqlite",
                    "path": "data/short_term.db",
                    "max_entries": 1000
                },
                "long_term": {
                    "type": "lancedb",
                    "path": "data/long_term",
                    "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                }
            },
            "security": {
                "encryption": {
                    "enabled": True,
                    "algorithm": "AES-256-GCM"
                },
                "scanner": {
                    "enabled": True,
                    "rules_path": "security/rules"
                }
            },
            "web": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 8000,
                "debug": False
            },
            "self_modification": {
                "enabled": True,
                "capability_iteration": {
                    "enabled": False
                },
                "sandbox": True,
                "backup_before_changes": True
            },
            "governance": {
                "allowed_paths": ["."],
                "require_confirmation": True,
                "audit_log": "logs/audit.jsonl"
            },
            "internet": {"enabled": False, "allowed_hosts": [], "max_download_bytes": 26214400},
            "network": {"allow_public_targets": False, "max_port_scan": 128}
        }
