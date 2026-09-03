"""Testes críticos para DecisionProtocol"""
import pytest
import asyncio
from core.decision_protocol import DecisionProtocol


def test_decision_protocol_uses_rules_for_high_confidence():
    """Testa que protocolo usa rules para alta confiança"""
    config = {}
    protocol = DecisionProtocol(config)

    semantic_result = {
        "intent": "list_files",
        "confidence": 0.8,
        "parameters": {}
    }
    context = {}

    decision = asyncio.run(protocol.decide(semantic_result, context))
    assert decision == "rules"


def test_decision_protocol_uses_llm_for_low_confidence():
    """Testa que protocolo usa LLM para baixa confiança"""
    config = {}
    protocol = DecisionProtocol(config)

    semantic_result = {
        "intent": "unknown",
        "confidence": 0.2,
        "parameters": {}
    }
    context = {}

    decision = asyncio.run(protocol.decide(semantic_result, context))
    assert decision == "llm"


def test_decision_protocol_contextual_critical_intents():
    """Testa que intenções críticas sempre usam rules"""
    config = {}
    protocol = DecisionProtocol(config)

    # Intenção crítica com confiança média
    semantic_result = {
        "intent": "delete_file",
        "confidence": 0.5,
        "parameters": {}
    }
    context = {}

    decision = asyncio.run(protocol.decide(semantic_result, context))
    assert decision == "rules"


def test_decision_protocol_contextual_conversational_intents():
    """Testa que intenções conversacionais preferem LLM"""
    config = {}
    protocol = DecisionProtocol(config)

    # Intenção conversacional com confiança média
    semantic_result = {
        "intent": "chat",
        "confidence": 0.5,
        "parameters": {}
    }
    context = {}

    decision = asyncio.run(protocol.decide(semantic_result, context))
    assert decision == "llm"


def test_decision_protocol_contextual_technical_intents():
    """Testa que intenções técnicas preferem rules"""
    config = {}
    protocol = DecisionProtocol(config)

    # Intenção técnica com confiança média
    semantic_result = {
        "intent": "scan_ports",
        "confidence": 0.5,
        "parameters": {}
    }
    context = {}

    decision = asyncio.run(protocol.decide(semantic_result, context))
    assert decision == "rules"


def test_decision_protocol_default_to_rules():
    """Testa que decisão padrão é rules"""
    config = {}
    protocol = DecisionProtocol(config)

    # Intenção genérica com confiança média
    semantic_result = {
        "intent": "generic_action",
        "confidence": 0.5,
        "parameters": {}
    }
    context = {}

    decision = asyncio.run(protocol.decide(semantic_result, context))
    assert decision == "rules"


def test_decision_protocol_evaluation():
    """Testa avaliação de decisão"""
    config = {}
    protocol = DecisionProtocol(config)

    # Avalia decisão sem feedback
    asyncio.run(protocol.evaluate_decision("rules", "resultado", None))

    # Avalia decisão com feedback
    asyncio.run(protocol.evaluate_decision("llm", "resultado", "bom resultado"))