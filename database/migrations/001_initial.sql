CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, display_name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id), created_at TEXT NOT NULL, ended_at TEXT
);
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY, session_id TEXT REFERENCES sessions(id), title TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id), role TEXT NOT NULL CHECK(role IN ('user','assistant','system')), content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, path TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, requested_action TEXT NOT NULL, parameters_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL, validation_json TEXT, result_json TEXT, project_id TEXT REFERENCES projects(id), created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS confirmations (
    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), requested_at TEXT NOT NULL, confirmed_at TEXT, decision TEXT NOT NULL, actor TEXT
);
CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), tool_name TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, result_json TEXT
);
CREATE TABLE IF NOT EXISTS security_scans (
    id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), target TEXT NOT NULL, scan_type TEXT NOT NULL, status TEXT NOT NULL, summary_json TEXT, created_at TEXT NOT NULL, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY, scan_id TEXT NOT NULL REFERENCES security_scans(id), severity TEXT, title TEXT NOT NULL, details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY, subject TEXT NOT NULL, permission TEXT NOT NULL, granted INTEGER NOT NULL, created_at TEXT NOT NULL, UNIQUE(subject, permission)
);
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY, action TEXT NOT NULL, outcome TEXT NOT NULL, authorization_json TEXT NOT NULL, parameters_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at);
