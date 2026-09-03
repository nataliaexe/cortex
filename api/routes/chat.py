from fastapi import APIRouter, HTTPException

from api.schemas.chat import ChatRequest, ChatResponse
from database.repositories.conversation_repository import ConversationRepository
from observability.metrics import metrics


def router(conversations: ConversationRepository, get_engine) -> APIRouter:
    api = APIRouter(prefix="/api", tags=["chat"])

    @api.post("/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest):
        conversation_id = payload.conversation_id or conversations.create(title=payload.message[:80])
        try:
            conversations.add_message(conversation_id, "user", payload.message)
            engine = get_engine()
            response = await engine.process_input(payload.message) if engine else "Motor principal não conectado"
            conversations.add_message(conversation_id, "assistant", response)
            metrics.increment("chat_requests")
            return ChatResponse(response=response, conversation_id=conversation_id)
        except Exception as error:
            raise HTTPException(status_code=500, detail="Não foi possível processar a mensagem.") from error

    @api.get("/conversations/{conversation_id}/messages")
    async def messages(conversation_id: str):
        return {"conversation_id": conversation_id, "messages": conversations.messages(conversation_id)}

    return api
