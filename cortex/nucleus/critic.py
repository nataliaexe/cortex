"""Critic. Revisa acoes destrutivas antes de executar.

Recebe tool, args e contexto. Devolve: aprovado/rejeitado + motivo + sugestao.
Usa modelo rapido e barato (Groq por padrao) para nao atrasar o loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from cortex.models.local import ChatMessage
from cortex.nucleus.router import AllProvidersFailed, Router
from cortex.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class CriticVerdict:
    approved: bool
    reason: str
    suggestion: str | None = None
    provider: str = ""
    model: str = ""


CRITIC_SYSTEM = """Voce e o critic do Cortex. Sua funcao: revisar acoes destrutivas antes que sejam executadas.

Voce recebe: a descricao da acao, os argumentos, e o contexto da conversa.

Sua tarefa: decidir se a acao parece segura e coerente com o que o usuario pediu.

Regras de aprovacao:
- APROVE se a acao e coerente com o pedido do usuario e o impacto parece contido.
- REJEITE se: a acao apaga dados sem o usuario ter pedido; modifica arquivos fora do escopo;
  executa comandos que nao correspondem ao pedido; ha sinal de erro de interpretacao.
- Em duvida, aprove com sugestao (ex: "confirme com o usuario antes de rodar").

Responda SEMPRE em JSON valido:
{"approved": true|false, "reason": "...", "suggestion": "..." | null}

Sem texto fora do JSON."""


class Critic:
    def __init__(self, router: Router) -> None:
        self.router = router

    async def review(
        self,
        tool: str,
        args: dict,
        context: str = "",
        user_request: str = "",
    ) -> CriticVerdict:
        import json
        user_content = (
            f"Acao: {tool}\n"
            f"Argumentos: {json.dumps(args, ensure_ascii=False)}\n"
        )
        if user_request:
            user_content += f"Pedido do usuario: {user_request}\n"
        if context:
            user_content += f"Contexto:\n{context}\n"

        messages = [
            ChatMessage(role="system", content=CRITIC_SYSTEM),
            ChatMessage(role="user", content=user_content),
        ]

        try:
            result = await self.router.route("classification", messages, temperature=0.1)
        except AllProvidersFailed as e:
            log.warning("critic_unavailable", error=str(e))
            # conservador: se nao consegue revisar, exige confirmacao humana
            return CriticVerdict(
                approved=False,
                reason="critic indisponivel; confirme manualmente",
                suggestion="revisar antes de executar",
            )

        text = result.text.strip()
        # extrai JSON
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return CriticVerdict(
                approved=True,
                reason="critic nao retornou JSON; aprovando por padrao",
                provider=result.provider,
                model=result.model,
            )
        try:
            data = json.loads(text[start : end + 1])
        except Exception:
            return CriticVerdict(
                approved=True,
                reason="critic retornou JSON invalido; aprovando por padrao",
                provider=result.provider,
                model=result.model,
            )

        return CriticVerdict(
            approved=bool(data.get("approved", True)),
            reason=str(data.get("reason", "")),
            suggestion=data.get("suggestion") or None,
            provider=result.provider,
            model=result.model,
        )
