-- Findings table — stores both deterministic and LLM-based analysis results.
-- One row per finding per message.

CREATE TABLE IF NOT EXISTS findings (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    analyzer VARCHAR(50) NOT NULL,          -- 'secrets', 'slopsquatting', 'pii', 'llm_trivial', 'llm_sensitivity', 'llm_complexity'
    category VARCHAR(50) NOT NULL,          -- 'security_leak', 'content_leak', 'supply_chain', 'usage_quality', 'complexity'
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',  -- 'critical', 'high', 'medium', 'low', 'info'
    title VARCHAR(500) NOT NULL,            -- human-readable finding title
    detail TEXT,                            -- explanation / context
    snippet TEXT,                           -- matched text or relevant excerpt
    confidence REAL NOT NULL DEFAULT 1.0,   -- 1.0 for deterministic, 0.0-1.0 for LLM
    meta JSONB NOT NULL DEFAULT '{}'::jsonb, -- analyzer-specific structured data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_findings_chat_id ON findings (chat_id);
CREATE INDEX IF NOT EXISTS ix_findings_analyzer ON findings (analyzer);
CREATE INDEX IF NOT EXISTS ix_findings_category ON findings (category);
CREATE INDEX IF NOT EXISTS ix_findings_severity ON findings (severity);

-- Aggregation view for dashboard
CREATE OR REPLACE VIEW findings_summary AS
SELECT
    f.analyzer,
    f.category,
    f.severity,
    COUNT(*) AS finding_count,
    c.provider,
    c.model_name
FROM findings f
JOIN chats c ON c.id = f.chat_id
GROUP BY f.analyzer, f.category, f.severity, c.provider, c.model_name
ORDER BY finding_count DESC;
