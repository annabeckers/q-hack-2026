-- Deterministic Analysis — Materialized Views for Dashboard
-- Following the pipeline pattern: tables → materialized views → API

-- 1. Overview stats (single row) — matches mv_dashboard_overview pattern
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_overview AS
SELECT
    COUNT(DISTINCT dcm.id) AS total_matches,
    COUNT(DISTINCT dcm.conversation_key) AS affected_conversations,
    COUNT(DISTINCT dcm.provider) AS total_providers,
    COUNT(DISTINCT dcm.company_category) AS total_categories,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.severity = 'critical') AS critical_matches,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.severity = 'high') AS high_matches,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.severity = 'medium') AS medium_matches,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.severity = 'low') AS low_matches,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.company_category = 'pii') AS pii_matches,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.company_category = 'secret') AS secret_matches,
    COUNT(DISTINCT dcm.id) FILTER (WHERE dcm.company_category = 'financial') AS financial_matches,
    MAX(dar.completed_at) AS last_analysis_run,
    NOW() AS refreshed_at
FROM deterministic_analysis_runs dar
LEFT JOIN deterministic_chat_matches dcm ON dcm.analysis_run_id = dar.id
WHERE dar.status = 'completed';

-- 2. Matches by category + severity + provider (for leak breakdown charts)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_by_category AS
SELECT
    dcm.company_category AS category,
    dcm.severity,
    dcm.provider,
    dcm.model_name,
    dcm.company_source_table,
    dcm.company_source_field,
    COUNT(*) AS match_count,
    COUNT(DISTINCT dcm.conversation_key) AS affected_conversations
FROM deterministic_chat_matches dcm
JOIN deterministic_analysis_runs dar ON dar.id = dcm.analysis_run_id
WHERE dar.status = 'completed'
GROUP BY dcm.company_category, dcm.severity, dcm.provider, dcm.model_name, 
         dcm.company_source_table, dcm.company_source_field
ORDER BY match_count DESC;

-- 3. Conversation summaries (pre-aggregated per conversation)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_conversations AS
SELECT
    dcm.conversation_key,
    MAX(dcm.conversation_title) AS conversation_title,
    MAX(dcm.provider) AS provider,
    MAX(dcm.model_name) AS model_name,
    MAX(dcm.department) AS department,
    COUNT(*) AS match_count,
    COUNT(*) FILTER (WHERE dcm.company_category = 'secret') AS secret_count,
    COUNT(*) FILTER (WHERE dcm.company_category = 'pii') AS pii_count,
    COUNT(*) FILTER (WHERE dcm.company_category = 'financial') AS financial_count,
    COUNT(*) FILTER (WHERE dcm.severity = 'critical') AS critical_count,
    COUNT(*) FILTER (WHERE dcm.severity = 'high') AS high_count,
    MAX(dcm.severity) AS highest_severity,  -- 'critical' > 'high' > 'medium' > 'low' alphabetically works
    MIN(dcm.message_timestamp) AS first_match_at,
    MAX(dcm.message_timestamp) AS last_match_at,
    ARRAY_AGG(DISTINCT dcm.company_label) AS labels,
    MAX(dar.completed_at) AS analysis_run_at
FROM deterministic_chat_matches dcm
JOIN deterministic_analysis_runs dar ON dar.id = dcm.analysis_run_id
WHERE dar.status = 'completed'
GROUP BY dcm.conversation_key
ORDER BY match_count DESC;

-- 4. Department stats (for department breakdown)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_by_department AS
SELECT
    COALESCE(dcm.department, 'unknown') AS department,
    dcm.provider,
    COUNT(*) AS match_count,
    COUNT(DISTINCT dcm.conversation_key) AS conversation_count,
    COUNT(*) FILTER (WHERE dcm.severity = 'critical') AS critical_count,
    COUNT(*) FILTER (WHERE dcm.severity = 'high') AS high_count,
    COUNT(*) FILTER (WHERE dcm.company_category = 'pii') AS pii_count,
    COUNT(*) FILTER (WHERE dcm.company_category = 'secret') AS secret_count
FROM deterministic_chat_matches dcm
JOIN deterministic_analysis_runs dar ON dar.id = dcm.analysis_run_id
WHERE dar.status = 'completed'
GROUP BY COALESCE(dcm.department, 'unknown'), dcm.provider
ORDER BY match_count DESC;

-- 5. Timeline (for trend sparklines)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_timeline AS
SELECT
    DATE(dcm.message_timestamp) AS day,
    dcm.company_category AS category,
    dcm.severity,
    dcm.provider,
    COUNT(*) AS match_count,
    COUNT(DISTINCT dcm.conversation_key) AS conversation_count
FROM deterministic_chat_matches dcm
JOIN deterministic_analysis_runs dar ON dar.id = dcm.analysis_run_id
WHERE dar.status = 'completed'
  AND dcm.message_timestamp IS NOT NULL
GROUP BY DATE(dcm.message_timestamp), dcm.company_category, dcm.severity, dcm.provider
ORDER BY day DESC;

-- 6. Top matches (for alert feed — critical/high severity)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_top_matches AS
SELECT
    dcm.id,
    dcm.department,
    dcm.source_file,
    dcm.conversation_key,
    dcm.conversation_title,
    dcm.provider,
    dcm.model_name,
    dcm.message_id,
    dcm.message_timestamp,
    dcm.author,
    dcm.role,
    dcm.company_label,
    dcm.company_category AS category,
    dcm.company_source_table,
    dcm.company_source_field,
    dcm.matched_text,
    dcm.match_context,
    dcm.severity,
    dcm.confidence,
    dcm.created_at,
    dar.completed_at AS analysis_run_at
FROM deterministic_chat_matches dcm
JOIN deterministic_analysis_runs dar ON dar.id = dcm.analysis_run_id
WHERE dar.status = 'completed'
  AND dcm.severity IN ('critical', 'high')
ORDER BY dcm.severity DESC, dcm.created_at DESC
LIMIT 100;

-- 7. Rules effectiveness (which rules are matching most)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deterministic_rule_stats AS
SELECT
    dcr.id AS rule_id,
    dcr.source_table,
    dcr.source_field,
    dcr.label,
    dcr.category AS rule_category,
    dcr.severity AS rule_severity,
    COUNT(dcm.id) AS match_count,
    COUNT(DISTINCT dcm.conversation_key) AS affected_conversations,
    MAX(dcm.created_at) AS last_match_at
FROM deterministic_company_rules dcr
LEFT JOIN deterministic_chat_matches dcm ON dcm.company_rule_id = dcr.id
GROUP BY dcr.id, dcr.source_table, dcr.source_field, dcr.label, 
         dcr.category, dcr.severity
ORDER BY match_count DESC;

-- Unique indexes required for CONCURRENT refresh
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_overview ON mv_deterministic_overview (refreshed_at);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_by_cat ON mv_deterministic_by_category 
    (category, severity, provider, model_name, company_source_table, company_source_field);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_conversations ON mv_deterministic_conversations (conversation_key);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_department ON mv_deterministic_by_department (department, provider);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_timeline ON mv_deterministic_timeline (day, category, severity, provider);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_top ON mv_deterministic_top_matches (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_det_rules ON mv_deterministic_rule_stats (rule_id);

-- Additional indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_mv_det_conv_dept ON mv_deterministic_conversations (department);
CREATE INDEX IF NOT EXISTS ix_mv_det_conv_provider ON mv_deterministic_conversations (provider);
CREATE INDEX IF NOT EXISTS ix_mv_det_conv_severity ON mv_deterministic_conversations (highest_severity);
CREATE INDEX IF NOT EXISTS ix_mv_det_top_dept ON mv_deterministic_top_matches (department);

-- Refresh function (called after analysis run)
CREATE OR REPLACE FUNCTION refresh_deterministic_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_overview;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_by_category;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_conversations;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_by_department;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_timeline;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_top_matches;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_deterministic_rule_stats;
END;
$$ LANGUAGE plpgsql;
