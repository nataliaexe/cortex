from __future__ import annotations

from database.connection import Database
from .base import new_id, now


class ConversationRepository:
    def __init__(self, database: Database): self.database = database

    def create(self, title: str | None = None, session_id: str | None = None) -> str:
        conversation_id = new_id()
        with self.database.connection() as conn:
            conn.execute("INSERT INTO conversations (id, session_id, title, created_at) VALUES (?, ?, ?, ?)", (conversation_id, session_id, title, now()))
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> str:
        message_id = new_id()
        with self.database.connection() as conn:
            conn.execute("INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)", (message_id, conversation_id, role, content, now()))
        return message_id

    def messages(self, conversation_id: str) -> list[dict]:
        with self.database.connection() as conn:
            return [dict(row) for row in conn.execute("SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at", (conversation_id,))]
