#!/usr/bin/env python3
"""
Gênesis Córtex - Secure Storage
Armazenamento seguro com criptografia AES-256-GCM
"""

import logging
import sqlite3
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import os


class SecureStorage:
    """Armazenamento seguro com criptografia"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.encryption_enabled = config.get("security", {}).get("encryption", {}).get("enabled", True)
        self.data_dir = Path(config.get("system", {}).get("data_dir", "data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Chave de criptografia (em produção, usar keyring adequado)
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Banco de dados de curto prazo
        self.db_path = self.data_dir / "short_term.db"
        self._init_database()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Obtém ou cria chave de criptografia"""
        key_path = self.data_dir / ".encryption_key"
        
        if key_path.exists():
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            key = AESGCM.generate_key(bit_length=256)
            with open(key_path, 'wb') as f:
                f.write(key)
            key_path.chmod(0o600)  # Apenas leitura/escrita pelo proprietário
            return key
            
    def _init_database(self):
        """Inicializa banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                response TEXT NOT NULL,
                context TEXT,
                encrypted INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                encrypted INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _encrypt(self, data: str) -> bytes:
        """Criptografa dados usando AES-256-GCM"""
        if not self.encryption_enabled:
            return data.encode('utf-8')
            
        aesgcm = AESGCM(self.encryption_key)
        nonce = os.urandom(12)  # 96-bit nonce
        data_bytes = data.encode('utf-8')
        encrypted = aesgcm.encrypt(nonce, data_bytes, None)
        return nonce + encrypted  # Prefixa nonce para descriptografia
        
    def _decrypt(self, encrypted_data: bytes) -> str:
        """Descriptografa dados usando AES-256-GCM"""
        if not self.encryption_enabled:
            return encrypted_data.decode('utf-8')
            
        aesgcm = AESGCM(self.encryption_key)
        nonce = encrypted_data[:12]  # Primeiros 12 bytes são o nonce
        ciphertext = encrypted_data[12:]
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')
        
    async def store_interaction(self, user_input: str, response: str, context: Dict[str, Any]) -> bool:
        """Armazena interação no banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            context_json = json.dumps(context) if context else None
            
            if self.encryption_enabled:
                user_input_encrypted = self._encrypt(user_input)
                response_encrypted = self._encrypt(response)
                context_encrypted = self._encrypt(context_json) if context_json else None
                
                cursor.execute('''
                    INSERT INTO interactions (timestamp, user_input, response, context, encrypted)
                    VALUES (?, ?, ?, ?, 1)
                ''', (timestamp, user_input_encrypted, response_encrypted, context_encrypted))
            else:
                cursor.execute('''
                    INSERT INTO interactions (timestamp, user_input, response, context, encrypted)
                    VALUES (?, ?, ?, ?, 0)
                ''', (timestamp, user_input, response, context_json))
                
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar interação: {e}")
            return False
            
    async def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera interações recentes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, user_input, response, context, encrypted
                FROM interactions
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            interactions = []
            for row in cursor.fetchall():
                interaction = {
                    "id": row[0],
                    "timestamp": row[1],
                    "user_input": self._decrypt(row[2]) if row[5] else row[2],
                    "response": self._decrypt(row[3]) if row[5] else row[3],
                    "context": json.loads(self._decrypt(row[4])) if row[4] and row[5] else json.loads(row[4]) if row[4] else None
                }
                interactions.append(interaction)
                
            conn.close()
            return interactions
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar interações: {e}")
            return []
            
    async def store_memory(self, content: str, tags: Optional[List[str]] = None) -> bool:
        """Armazena memória de longo prazo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            tags_json = json.dumps(tags) if tags else None
            
            if self.encryption_enabled:
                content_encrypted = self._encrypt(content)
                tags_encrypted = self._encrypt(tags_json) if tags_json else None
                
                cursor.execute('''
                    INSERT INTO memories (timestamp, content, tags, encrypted)
                    VALUES (?, ?, ?, 1)
                ''', (timestamp, content_encrypted, tags_encrypted))
            else:
                cursor.execute('''
                    INSERT INTO memories (timestamp, content, tags, encrypted)
                    VALUES (?, ?, ?, 0)
                ''', (timestamp, content, tags_json))
                
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar memória: {e}")
            return False
            
    async def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca memórias por conteúdo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, content, tags, encrypted
                FROM memories
                ORDER BY timestamp DESC
            ''')
            
            memories = []
            for row in cursor.fetchall():
                content = self._decrypt(row[2]) if row[4] else row[2]
                
                # Busca simples por substring
                if query.lower() in content.lower():
                    memory = {
                        "id": row[0],
                        "timestamp": row[1],
                        "content": content,
                        "tags": json.loads(self._decrypt(row[3])) if row[3] and row[4] else json.loads(row[3]) if row[3] else []
                    }
                    memories.append(memory)
                    
                    if len(memories) >= limit:
                        break
                        
            conn.close()
            return memories
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar memórias: {e}")
            return []