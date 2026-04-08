-- Deterministic company-data vs chat-data analysis schema

CREATE TABLE IF NOT EXISTS deterministic_analysis_runs (
    id                  TEXT PRIMARY KEY,
    source_message_count INTEGER NOT NULL,
    rule_count          INTEGER NOT NULL,
    match_count         INTEGER NOT NULL,
    status              TEXT NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deterministic_company_rules (
    id                  TEXT PRIMARY KEY,
    source_table        TEXT NOT NULL,
    source_record_id    TEXT NOT NULL,
    source_field        TEXT NOT NULL,
    label               TEXT NOT NULL,
    category            TEXT NOT NULL,
    severity            TEXT NOT NULL,
    pattern             TEXT NOT NULL,
    value               TEXT NOT NULL,
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deterministic_chat_matches (
    id                  TEXT PRIMARY KEY,
    analysis_run_id     TEXT NOT NULL REFERENCES deterministic_analysis_runs(id) ON DELETE CASCADE,
    source_file         TEXT NOT NULL,
    conversation_key    TEXT NOT NULL,
    conversation_title  TEXT,
    provider            TEXT NOT NULL,
    model_name          TEXT,
    message_id          TEXT NOT NULL,
    message_timestamp   TIMESTAMPTZ,
    author              TEXT NOT NULL,
    role                TEXT NOT NULL,
    source_field        TEXT NOT NULL,
    company_rule_id     TEXT NOT NULL REFERENCES deterministic_company_rules(id),
    company_label       TEXT NOT NULL,
    company_category    TEXT NOT NULL,
    company_source_table TEXT NOT NULL,
    company_source_field TEXT NOT NULL,
    matched_text        TEXT NOT NULL,
    match_context       TEXT NOT NULL,
    severity            TEXT NOT NULL,
    confidence          NUMERIC(4, 2) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (analysis_run_id, source_file, conversation_key, message_id, company_rule_id, matched_text)
);

CREATE INDEX IF NOT EXISTS ix_deterministic_matches_run ON deterministic_chat_matches (analysis_run_id);
CREATE INDEX IF NOT EXISTS ix_deterministic_matches_conversation ON deterministic_chat_matches (conversation_key);
CREATE INDEX IF NOT EXISTS ix_deterministic_matches_provider ON deterministic_chat_matches (provider);
CREATE INDEX IF NOT EXISTS ix_deterministic_matches_category ON deterministic_chat_matches (company_category);

CREATE TABLE IF NOT EXISTS deterministic_conversation_summaries (
    analysis_run_id     TEXT NOT NULL REFERENCES deterministic_analysis_runs(id) ON DELETE CASCADE,
    conversation_key    TEXT NOT NULL,
    provider            TEXT NOT NULL,
    model_name          TEXT,
    match_count         INTEGER NOT NULL,
    secret_count        INTEGER NOT NULL,
    pii_count           INTEGER NOT NULL,
    financial_count     INTEGER NOT NULL,
    labels_json         TEXT NOT NULL,
    highest_severity    TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (analysis_run_id, conversation_key)
);

CREATE INDEX IF NOT EXISTS ix_deterministic_summary_conversation ON deterministic_conversation_summaries (conversation_key);
