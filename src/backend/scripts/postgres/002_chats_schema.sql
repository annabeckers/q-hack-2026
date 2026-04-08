-- Chat exports import schema (business analytics only)

CREATE TABLE IF NOT EXISTS chats (
    id BIGSERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    source_format VARCHAR(20) NOT NULL DEFAULT 'json',
    provider VARCHAR(50) NOT NULL,
    conversation_key TEXT NOT NULL,
    conversation_title TEXT,
    conversation_slug TEXT,
    export_author VARCHAR(50),
    model_name VARCHAR(100),
    conversation_timestamp TIMESTAMPTZ,
    message_id TEXT NOT NULL,
    parent_message_id TEXT,
    message_index INTEGER NOT NULL,
    message_timestamp TIMESTAMPTZ,
    author VARCHAR(20) NOT NULL DEFAULT 'user',
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    language VARCHAR(50),
    user_text TEXT NOT NULL,
    user_text_clean TEXT NOT NULL,
    user_text_hash CHAR(64) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_file, conversation_key, message_id)
);

ALTER TABLE chats ADD COLUMN IF NOT EXISTS author VARCHAR(20) NOT NULL DEFAULT 'user';

CREATE INDEX IF NOT EXISTS ix_chats_provider ON chats (provider);
CREATE INDEX IF NOT EXISTS ix_chats_conversation_ts ON chats (conversation_timestamp);
CREATE INDEX IF NOT EXISTS ix_chats_user_text_hash ON chats (user_text_hash);
