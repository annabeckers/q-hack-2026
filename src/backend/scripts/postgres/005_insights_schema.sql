CREATE TABLE IF NOT EXISTS conversation_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id BIGINT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_insights_chat_id ON conversation_insights(chat_id);
CREATE INDEX IF NOT EXISTS idx_insights_score ON conversation_insights(risk_score);
