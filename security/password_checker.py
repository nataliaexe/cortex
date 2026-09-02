#!/usr/bin/env python3
"""
Gênesis Córtex - Password Checker
Verificador de senhas fracas
"""

import logging
import hashlib
import secrets
import string
from typing import Dict, Any, List
from pathlib import Path
import re


class PasswordChecker:
    """Verificador de senhas"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Lista de senhas comuns (simulada)
        self.common_passwords = self._load_common_passwords()
        
    def _load_common_passwords(self) -> set:
        """Carrega lista de senhas comuns"""
        common_passwords = {
            "123456", "password", "12345678", "qwerty", "123456789",
            "12345", "1234", "111111", "1234567", "dragon", "123123",
            "baseball", "abc123", "football", "monkey", "letmein",
            "696969", "shadow", "master", "666666", "qwertyuiop",
            "123321", "mustang", "1234567890", "michael", "654321",
            "pussy", "superman", "1qaz2wsx", "7777777", "fuckyou",
            "121212", "000000", "qazwsx", "123qwe", "killer", "trustno1",
            "jordan", "jennifer", "zxcvbnm", "asdfgh", "hunter", "buster",
            "soccer", "harley", "batman", "andrew", "tigger", "sunshine",
            "iloveyou", "2000", "charlie", "robert", "thomas", "hockey",
            "ranger", "daniel", "starwars", "klaster", "112233", "george",
            "computer", "michelle", "jessica", "pepper", "1111", "zxcvbn",
            "555555", "11111111", "131313", "freedom", "777777", "pass",
            "maggie", "159753", "aaaaaa", "ginger", "princess", "joshua",
            "cheese", "amanda", "summer", "love", "ashley", "6969",
            "nicole", "chelsea", "biteme", "matthew", "access", "yankees",
            "987654321", "dallas", "austin", "thunder", "taylor", "matrix"
        }
        
        # Tenta carregar de arquivo se existir
        common_passwords_file = Path("security/common_passwords.txt")
        if common_passwords_file.exists():
            try:
                with open(common_passwords_file, 'r', encoding='utf-8') as f:
                    common_passwords.update(line.strip() for line in f)
            except Exception as e:
                self.logger.warning(f"Erro ao carregar senhas comuns: {e}")
                
        return common_passwords
        
    def check_password(self, password: str) -> Dict[str, Any]:
        """Verifica força de uma senha"""
        result = {
            "password": password,
            "strength": "unknown",
            "score": 0,
            "issues": [],
            "suggestions": []
        }
        
        # Verificações básicas
        if len(password) < 8:
            result["issues"].append("Senha muito curta (mínimo 8 caracteres)")
            result["suggestions"].append("Use pelo menos 8 caracteres")
            
        if password.lower() in self.common_passwords:
            result["issues"].append("Senha muito comum")
            result["suggestions"].append("Use uma senha mais única")
            
        # Verifica padrões comuns
        if self._has_common_pattern(password):
            result["issues"].append("Senha contém padrão comum")
            result["suggestions"].append("Evite sequências ou repetições")
            
        # Verifica complexidade
        complexity = self._check_complexity(password)
        result["complexity"] = complexity
        
        if not complexity["has_uppercase"]:
            result["issues"].append("Falta letras maiúsculas")
            result["suggestions"].append("Adicione letras maiúsculas")
            
        if not complexity["has_lowercase"]:
            result["issues"].append("Falta letras minúsculas")
            result["suggestions"].append("Adicione letras minúsculas")
            
        if not complexity["has_digits"]:
            result["issues"].append("Falta números")
            result["suggestions"].append("Adicione números")
            
        if not complexity["has_special"]:
            result["issues"].append("Falta caracteres especiais")
            result["suggestions"].append("Adicione caracteres especiais (!@#$% etc)")
            
        # Calcula score
        result["score"] = self._calculate_score(password, complexity)
        
        # Determina força
        if result["score"] >= 80:
            result["strength"] = "strong"
        elif result["score"] >= 60:
            result["strength"] = "medium"
        elif result["score"] >= 40:
            result["strength"] = "weak"
        else:
            result["strength"] = "very_weak"
            
        return result
        
    def _has_common_pattern(self, password: str) -> bool:
        """Verifica padrões comuns"""
        # Sequências
        sequences = [
            "0123456789", "9876543210",
            "abcdefghijklmnopqrstuvwxyz", "zyxwvutsrqponmlkjihgfedcba",
            "qwertyuiop", "asdfghjkl", "zxcvbnm"
        ]
        
        password_lower = password.lower()
        
        for sequence in sequences:
            if sequence in password_lower or sequence[::-1] in password_lower:
                return True
                
        # Repetições
        if len(set(password)) < len(password) / 2:
            return True
            
        return False
        
    def _check_complexity(self, password: str) -> Dict[str, bool]:
        """Verifica complexidade da senha"""
        return {
            "has_uppercase": any(c.isupper() for c in password),
            "has_lowercase": any(c.islower() for c in password),
            "has_digits": any(c.isdigit() for c in password),
            "has_special": any(not c.isalnum() for c in password)
        }
        
    def _calculate_score(self, password: str, complexity: Dict[str, bool]) -> int:
        """Calcula score da senha"""
        score = 0
        
        # Comprimento
        score += min(len(password) * 4, 40)
        
        # Complexidade
        if complexity["has_uppercase"]:
            score += 10
        if complexity["has_lowercase"]:
            score += 10
        if complexity["has_digits"]:
            score += 10
        if complexity["has_special"]:
            score += 15
            
        # Bônus por combinação
        combo_count = sum(complexity.values())
        if combo_count >= 3:
            score += 10
        if combo_count == 4:
            score += 5
            
        return min(score, 100)
        
    def check_password_hash(self, password_hash: str, hash_type: str = "sha256") -> Dict[str, Any]:
        """Verifica se hash de senha está em lista de vazamentos"""
        # Implementação simplificada - na prática usaria APIs como HaveIBeenPwned
        return {
            "hash": password_hash,
            "hash_type": hash_type,
            "in_breach_list": False,
            "note": "Verificação completa requer integração com HaveIBeenPwned API"
        }
        
    def generate_strong_password(self, length: int = 16) -> str:
        """Gera senha forte"""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Garante que tem pelo menos um de cada tipo
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        if not any(not c.isalnum() for c in password):
            password = password[:-1] + secrets.choice(string.punctuation)
            
        return password