from database.connection import Database
from database.repositories.conversation_repository import ConversationRepository
from database.repositories.task_repository import TaskRepository


def test_database_persists_messages_and_tasks(tmp_path):
    database = Database(tmp_path / "cortex.db"); database.initialize()
    conversations = ConversationRepository(database)
    conversation_id = conversations.create("teste")
    conversations.add_message(conversation_id, "user", "olá")
    assert conversations.messages(conversation_id)[0]["content"] == "olá"
    tasks = TaskRepository(database)
    task = tasks.create("network_diagnostic", {"host": "127.0.0.1"})
    tasks.update(task["id"], "approved", {"allowed": True})
    assert tasks.get(task["id"])["status"] == "approved"
