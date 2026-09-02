#!/usr/bin/env python3
"""
Gênesis Córtex - Safe Editor
Editor de código com backup + rollback
"""

import logging
import shutil
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import hashlib


class SafeEditor:
    """Editor seguro com backup automático"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.backup_enabled = config.get("self_modification", {}).get("backup_before_changes", True)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def edit_file(self, file_path: str, old_content: str, new_content: str, description: str = "") -> bool:
        """Edita arquivo com backup automático"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"Arquivo {file_path} não existe")
            return False
            
        # Cria backup se habilitado
        if self.backup_enabled:
            backup_path = await self._create_backup(file_path, description)
            if not backup_path:
                self.logger.error("Falha ao criar backup")
                return False
                
        # Verifica se conteúdo original corresponde
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
                
            if old_content not in current_content:
                self.logger.warning("Conteúdo original não corresponde ao atual")
                if self.backup_enabled:
                    self.logger.info("Backup mantido para segurança")
                    
        except Exception as e:
            self.logger.error(f"Erro ao verificar conteúdo atual: {e}")
            return False
            
        # Aplica edição
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            self.logger.info(f"Arquivo {file_path} editado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao editar arquivo: {e}")
            
            # Tenta rollback se backup existe
            if self.backup_enabled and backup_path:
                await self._restore_backup(file_path, backup_path)
                
            return False
            
    async def _create_backup(self, file_path: Path, description: str) -> Optional[Path]:
        """Cria backup do arquivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}_{timestamp}.bak"
            backup_path = self.backup_dir / backup_name
            
            # Copia arquivo
            shutil.copy2(file_path, backup_path)
            
            # Cria metadados do backup
            metadata = {
                "original_file": str(file_path),
                "backup_file": str(backup_path),
                "timestamp": timestamp,
                "description": description,
                "hash": self._calculate_hash(file_path)
            }
            
            metadata_file = backup_path.with_suffix('.bak.meta')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, indent=2)
                
            self.logger.info(f"Backup criado: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return None
            
    async def _restore_backup(self, file_path: Path, backup_path: Path) -> bool:
        """Restaura arquivo do backup"""
        try:
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"Backup restaurado: {backup_path} -> {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            return False
            
    async def rollback(self, file_path: str, backup_timestamp: str) -> bool:
        """Rollback para backup específico"""
        file_path = Path(file_path)
        backup_name = f"{file_path.name}_{backup_timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            self.logger.error(f"Backup {backup_path} não encontrado")
            return False
            
        return await self._restore_backup(file_path, backup_path)
        
    async def list_backups(self, file_path: str) -> list:
        """Lista backups disponíveis para um arquivo"""
        file_path = Path(file_path)
        backups = []
        
        for backup_file in self.backup_dir.glob(f"{file_path.name}_*.bak"):
            try:
                metadata_file = backup_file.with_suffix('.bak.meta')
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        import json
                        metadata = json.load(f)
                    backups.append(metadata)
                else:
                    backups.append({
                        "backup_file": str(backup_file),
                        "timestamp": backup_file.stem.split('_')[-1]
                    })
            except Exception as e:
                self.logger.warning(f"Erro ao ler metadados de {backup_file}: {e}")
                
        return sorted(backups, key=lambda x: x.get("timestamp", ""), reverse=True)
        
    async def cleanup_old_backups(self, days: int = 7) -> int:
        """Remove backups antigos"""
        cutoff_time = datetime.now().timestamp() - (days * 86400)
        removed = 0
        
        for backup_file in self.backup_dir.glob("*.bak"):
            try:
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    # Remove metadados também
                    metadata_file = backup_file.with_suffix('.bak.meta')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    removed += 1
            except Exception as e:
                self.logger.warning(f"Erro ao remover backup antigo {backup_file}: {e}")
                
        self.logger.info(f"{removed} backups antigos removidos")
        return removed
        
    def _calculate_hash(self, file_path: Path) -> str:
        """Calcula hash do arquivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    async def verify_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Verifica integridade do arquivo"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
            
        current_hash = self._calculate_hash(file_path)
        return current_hash == expected_hash