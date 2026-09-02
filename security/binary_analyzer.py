#!/usr/bin/env python3
"""
Gênesis Córtex - Binary Analyzer
Análise estática de binários ELF/PE
"""

import logging
import struct
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib


class BinaryAnalyzer:
    """Analisador de binários"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Analisa um binário"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": f"Arquivo {file_path} não encontrado"}
            
        # Calcula hash
        file_hash = self._calculate_hash(file_path)
        
        # Detecta tipo de binário
        binary_type = self._detect_binary_type(file_path)
        
        if binary_type == "elf":
            return self._analyze_elf(file_path, file_hash)
        elif binary_type == "pe":
            return self._analyze_pe(file_path, file_hash)
        elif binary_type == "macho":
            return self._analyze_macho(file_path, file_hash)
        else:
            return {"error": f"Tipo de binário não suportado: {binary_type}"}
            
    def _calculate_hash(self, file_path: Path) -> Dict[str, str]:
        """Calcula hashes do arquivo"""
        hashes = {}
        
        # SHA-256
        sha256_hash = hashlib.sha256()
        # MD5
        md5_hash = hashlib.md5()
        # SHA-1
        sha1_hash = hashlib.sha1()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                md5_hash.update(byte_block)
                sha1_hash.update(byte_block)
                
        hashes["sha256"] = sha256_hash.hexdigest()
        hashes["md5"] = md5_hash.hexdigest()
        hashes["sha1"] = sha1_hash.hexdigest()
        
        return hashes
        
    def _detect_binary_type(self, file_path: Path) -> Optional[str]:
        """Detecta tipo de binário pelos magic bytes"""
        try:
            with open(file_path, "rb") as f:
                magic = f.read(4)
                
            if magic[:4] == b'\x7fELF':
                return "elf"
            elif magic[:2] == b'MZ':
                return "pe"
            elif magic[:4] in [b'\xfe\xed\xfa\xce', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe']:
                return "macho"
            else:
                return "unknown"
                
        except Exception as e:
            self.logger.error(f"Erro ao detectar tipo de binário: {e}")
            return None
            
    def _analyze_elf(self, file_path: Path, file_hash: Dict[str, str]) -> Dict[str, Any]:
        """Analisa binário ELF"""
        try:
            with open(file_path, "rb") as f:
                # ELF Header
                elf_magic = f.read(4)
                if elf_magic != b'\x7fELF':
                    return {"error": "Arquivo não é ELF válido"}
                    
                f.seek(16)  # Pula para o campo de tipo
                e_type = struct.unpack('H', f.read(2))[0]
                
                f.seek(18)  # Campo de máquina
                e_machine = struct.unpack('H', f.read(2))[0]
                
                f.seek(36)  # Campo de entry point
                e_entry = struct.unpack('Q', f.read(8))[0]
                
                f.seek(40)  # Campo de program header offset
                e_phoff = struct.unpack('Q', f.read(8))[0]
                
                f.seek(48)  # Campo de section header offset
                e_shoff = struct.unpack('Q', f.read(8))[0]
                
                f.seek(56)  # Campo de flags
                e_flags = struct.unpack('I', f.read(4))[0]
                
            # Interpretação dos campos
            type_map = {1: "REL", 2: "EXEC", 3: "DYN", 4: "CORE"}
            machine_map = {
                0x3e: "x86-64",
                0x03: "x86",
                0xb7: "AArch64",
                0x28: "ARM",
                0xf3: "RISC-V"
            }
            
            analysis = {
                "type": "ELF",
                "hashes": file_hash,
                "file_type": type_map.get(e_type, "UNKNOWN"),
                "architecture": machine_map.get(e_machine, "UNKNOWN"),
                "entry_point": hex(e_entry),
                "program_header_offset": hex(e_phoff),
                "section_header_offset": hex(e_shoff),
                "flags": hex(e_flags),
                "security_flags": [],
                "suspicious_sections": []
            }
            
            # Verifica flags de segurança
            if e_flags & 0x1:  # DF_ORIGIN
                analysis["security_flags"].append("ORIGIN")
                
            # Busca seções suspeitas
            suspicious_sections = [".text", ".data", ".bss", ".rodata"]
            # Implementação simplificada - na prática seria necessário ler section headers
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar ELF: {e}")
            return {"error": f"Erro ao analisar ELF: {e}"}
            
    def _analyze_pe(self, file_path: Path, file_hash: Dict[str, str]) -> Dict[str, Any]:
        """Analisa binário PE (Windows)"""
        try:
            with open(file_path, "rb") as f:
                # DOS Header
                dos_magic = f.read(2)
                if dos_magic != b'MZ':
                    return {"error": "Arquivo não é PE válido"}
                    
                # PE Header offset
                f.seek(0x3C)
                pe_offset = struct.unpack('I', f.read(4))[0]
                
                # PE Signature
                f.seek(pe_offset)
                pe_magic = f.read(4)
                if pe_magic != b'PE\x00\x00':
                    return {"error": "Assinatura PE inválida"}
                    
                # COFF Header
                f.seek(pe_offset + 4)
                machine = struct.unpack('H', f.read(2))[0]
                num_sections = struct.unpack('H', f.read(2))[0]
                
                # Optional Header
                f.seek(pe_offset + 20)
                magic = struct.unpack('H', f.read(2))[0]
                
                if magic == 0x10b:  # PE32
                    entry_point = struct.unpack('I', f.read(4))[0]
                    f.seek(pe_offset + 24)
                    image_base = struct.unpack('I', f.read(4))[0]
                elif magic == 0x20b:  # PE32+
                    entry_point = struct.unpack('I', f.read(4))[0]
                    f.seek(pe_offset + 24)
                    image_base = struct.unpack('Q', f.read(8))[0]
                else:
                    return {"error": "Tipo PE não suportado"}
                    
            # Interpretação dos campos
            machine_map = {
                0x014c: "x86",
                0x8664: "x86-64",
                0x1c0: "ARM",
                0xaa64: "AArch64"
            }
            
            analysis = {
                "type": "PE",
                "hashes": file_hash,
                "architecture": machine_map.get(machine, "UNKNOWN"),
                "entry_point": hex(entry_point),
                "image_base": hex(image_base),
                "num_sections": num_sections,
                "security_flags": [],
                "suspicious_sections": []
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar PE: {e}")
            return {"error": f"Erro ao analisar PE: {e}"}
            
    def _analyze_macho(self, file_path: Path, file_hash: Dict[str, str]) -> Dict[str, Any]:
        """Analisa binário Mach-O (macOS)"""
        try:
            with open(file_path, "rb") as f:
                magic = f.read(4)
                
                magic_map = {
                    b'\xfe\xed\xfa\xce': "Mach-O (32-bit)",
                    b'\xfe\xed\xfa\xcf': "Mach-O (64-bit)",
                    b'\xcf\xfa\xed\xfe': "Mach-O (64-bit, reversed)",
                    b'\xce\xfa\xed\xfe': "Mach-O (32-bit, reversed)"
                }
                
                file_type = magic_map.get(magic, "UNKNOWN")
                
                # CPU Type
                cputype = struct.unpack('I', f.read(4))[0]
                
                cpu_map = {
                    0x7: "x86",
                    0x1000007: "x86-64",
                    0xc: "ARM",
                    0x100000c: "AArch64",
                    0x1000012: "AArch64 (Apple Silicon)"
                }
                
            analysis = {
                "type": "Mach-O",
                "hashes": file_hash,
                "file_type": file_type,
                "architecture": cpu_map.get(cputype, "UNKNOWN"),
                "security_flags": [],
                "suspicious_sections": []
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar Mach-O: {e}")
            return {"error": f"Erro ao analisar Mach-O: {e}"}
            
    def extract_strings(self, file_path: str, min_length: int = 4) -> List[str]:
        """Extrai strings legíveis de um binário"""
        strings = []
        
        try:
            with open(file_path, "rb") as f:
                current_string = ""
                
                while True:
                    byte = f.read(1)
                    if not byte:
                        break
                        
                    char = byte[0]
                    if 32 <= char <= 126:  # Caracteres imprimíveis ASCII
                        current_string += chr(char)
                    else:
                        if len(current_string) >= min_length:
                            strings.append(current_string)
                        current_string = ""
                        
                if len(current_string) >= min_length:
                    strings.append(current_string)
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair strings: {e}")
            
        return strings
        
    def check_packed(self, file_path: str) -> Dict[str, Any]:
        """Verifica se binário está empacotado"""
        strings = self.extract_strings(file_path, min_length=8)
        
        packer_signatures = [
            "UPX",
            "ASPack",
            "PECompact",
            "Themida",
            "VMProtect",
            "Armadillo",
            "NSPack",
            "PEiD"
        ]
        
        detected_packers = []
        for string in strings:
            for packer in packer_signatures:
                if packer.lower() in string.lower():
                    detected_packers.append(packer)
                    
        return {
            "packed": len(detected_packers) > 0,
            "detected_packers": list(set(detected_packers)),
            "total_strings": len(strings)
        }