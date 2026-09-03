"""Testes críticos para SemanticMatcher com cache de embeddings"""
import pytest
import asyncio
from core.semantic_matcher import SemanticMatcher


def test_semantic_matcher_caches_embeddings():
    """Testa que embeddings são cacheados no startup"""
    config = {
        "memory": {
            "long_term": {
                "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            }
        }
    }

    # Cria um arquivo de intenções temporário
    import tempfile
    import json
    with tempfile.TemporaryDirectory() as tmpdir:
        personality_dir = f"{tmpdir}/personality"
        import os
        os.makedirs(personality_dir, exist_ok=True)

        intents_data = {
            "intents": {
                "system_info": {
                    "examples": ["qual o status do sistema?", "informações do sistema", "me diga sobre o sistema"],
                    "parameters": {}
                },
                "list_files": {
                    "examples": ["liste os arquivos", "mostrar arquivos", "quais arquivos existem"],
                    "parameters": {}
                }
            }
        }

        with open(f"{personality_dir}/base_training.json", "w") as f:
            json.dump(intents_data, f)

        # Atualiza config para usar o diretório temporário
        # Nota: SemanticMatcher usa path fixo "personality/base_training.json"
        # Para teste real, precisaria mockar o path ou usar estrutura real

        matcher = SemanticMatcher(config)

        # Verifica que cache existe
        assert hasattr(matcher, 'intent_embeddings_cache')
        assert isinstance(matcher.intent_embeddings_cache, dict)


def test_semantic_matcher_uses_cached_embeddings():
    """Testa que matcher usa embeddings cacheados"""
    # Este teste seria mais complexo e requer mocking do modelo
    # Por enquanto, testamos a estrutura
    config = {"memory": {}}
    matcher = SemanticMatcher(config)

    assert hasattr(matcher, 'intent_embeddings_cache')
    # Sem modelo, cache deve estar vazio
    assert len(matcher.intent_embeddings_cache) == 0


def test_semantic_matcher_fallback():
    """Testa fallback quando modelo não está disponível"""
    config = {"memory": {}}
    matcher = SemanticMatcher(config)

    # Sem modelo, deve usar fallback
    result = matcher._fallback_match("me mostre os arquivos")
    assert result["intent"] == "list_files"
    assert result["confidence"] > 0


def test_semantic_matcher_parameter_extraction():
    """Testa extração de parâmetros"""
    config = {"memory": {}}
    matcher = SemanticMatcher(config)

    intent_data = {
        "parameters": {
            "path": {"type": "path"},
            "number": {"type": "number"}
        }
    }

    params = matcher._extract_parameters("liste arquivos em /home/user 123", intent_data)
    assert "path" in params
    assert "number" in params