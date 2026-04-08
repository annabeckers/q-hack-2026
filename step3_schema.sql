-- Step 3: PostgreSQL schema for AI usage tracking
-- Run with: psql -U postgres -d ai_usage -f step3_schema.sql

CREATE TABLE IF NOT EXISTS tools_usage (
    id              TEXT PRIMARY KEY,
    user_id_hash    TEXT        NOT NULL,
    department_id   TEXT        NOT NULL,
    tool_name       TEXT        NOT NULL,
    model_name      TEXT        NOT NULL,
    usage_start     TIMESTAMPTZ NOT NULL,
    usage_end       TIMESTAMPTZ NOT NULL,
    token_count     INTEGER     NOT NULL CHECK (token_count >= 0),
    cost            NUMERIC(10, 4) NOT NULL CHECK (cost >= 0),
    purpose         TEXT,
    region          TEXT,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for common query patterns
CREATE INDEX IF NOT EXISTS idx_tools_usage_department  ON tools_usage (department_id);
CREATE INDEX IF NOT EXISTS idx_tools_usage_tool        ON tools_usage (tool_name);
CREATE INDEX IF NOT EXISTS idx_tools_usage_model       ON tools_usage (model_name);
CREATE INDEX IF NOT EXISTS idx_tools_usage_start       ON tools_usage (usage_start);

-- Optional: aggregated view per department per day
CREATE OR REPLACE VIEW daily_department_summary AS
SELECT
    DATE(usage_start)   AS day,
    department_id,
    tool_name,
    model_name,
    COUNT(*)            AS event_count,
    SUM(token_count)    AS total_tokens,
    ROUND(SUM(cost), 4) AS total_cost
FROM tools_usage
GROUP BY DATE(usage_start), department_id, tool_name, model_name
ORDER BY day DESC, total_cost DESC;
