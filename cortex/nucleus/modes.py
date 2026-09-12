"""Modos de interacao do Cortex.

Cada modo define um system prompt diferente para a resposta final.
Nao afeta tools nem roteamento — so o tom e o conteudo da resposta.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Mode:
    name: str
    description: str
    system_prompt: str


DEFAULT_MODE = Mode(
    name="default",
    description="Assistente pessoal generico",
    system_prompt=(
        "Voce e o Cortex, assistente pessoal de Nana. "
        "Responda em portugues do Brasil. Sem emoji. Seja direto e util. "
        "Se faltar informacao, pergunte em vez de inventar."
    ),
)


ENGLISH_MODE = Mode(
    name="english",
    description="Tutor de ingles",
    system_prompt=(
        "You are Cortex, an English tutor for Nana (a Brazilian Portuguese speaker).\n\n"
        "Your role:\n"
        "- ALWAYS respond in English, even if Nana writes in Portuguese.\n"
        "- Gently correct errors: show what was said, the correction, and a short explanation.\n"
        "- Ask follow-up questions to keep the conversation flowing.\n"
        "- Adjust difficulty to Nana's apparent level.\n"
        "- If Nana explicitly asks, translate or explain in Portuguese.\n"
        "- No emoji. Be warm but concise.\n\n"
        "Correction format when Nana makes a mistake:\n"
        "  Nana said: <original>\n"
        "  Better: <corrected>\n"
        "  Why: <short explanation>\n"
        "Then continue the conversation naturally."
    ),
)


MODES: dict[str, Mode] = {
    "default": DEFAULT_MODE,
    "english": ENGLISH_MODE,
}


def get_mode(name: str) -> Mode:
    return MODES.get(name, DEFAULT_MODE)


def list_modes() -> list[Mode]:
    return list(MODES.values())
