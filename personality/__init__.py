#!/usr/bin/env python3
"""
Gênesis Córtex - Personality Module
Módulo de personalidade e configurações
"""

import json
from pathlib import Path

__all__ = ['load_base_training', 'load_custom_overrides']

def load_base_training():
    """Carrega configuração base de treinamento"""
    base_path = Path("personality/base_training.json")
    if base_path.exists():
        with open(base_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_custom_overrides():
    """Carrega overrides personalizados"""
    overrides_path = Path("personality/custom_overrides.json")
    if overrides_path.exists():
        with open(overrides_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}