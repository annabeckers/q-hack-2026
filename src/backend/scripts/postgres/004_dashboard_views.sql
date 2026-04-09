-- Dashboard read layer — materialized views for fast frontend queries.
-- Refreshed by the analysis worker after each run.

-- 1. Overall stats (single row)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_overview AS
SELECT
    COUNT(DISTINCT c.id) AS total_messages,
    COUNT(DISTINCT c.conversation_key) AS total_conversations,
    COUNT(DISTINCT c.provider) AS total_providers,
    COUNT(DISTINCT f.id) AS total_findings,
    COUNT(DISTINCT f.id) FILTER (WHERE f.severity = 'critical') AS critical_findings,
    COUNT(DISTINCT f.id) FILTER (WHERE f.severity = 'high') AS high_findings,
    COUNT(DISTINCT f.id) FILTER (WHERE f.severity = 'medium') AS medium_findings,
    COUNT(DISTINCT f.id) FILTER (WHERE f.severity = 'low') AS low_findings,
    COUNT(DISTINCT c.id) FILTER (WHERE EXISTS (
        SELECT 1 FROM findings ff WHERE ff.chat_id = c.id
    )) AS analyzed_messages,
    COUNT(DISTINCT c.id) FILTER (WHERE NOT EXISTS (
        SELECT 1 FROM findings ff WHERE ff.chat_id = c.id
    )) AS pending_messages,
    AVG(ci.risk_score) AS average_risk_score,
    NOW() AS refreshed_at
FROM chats c
LEFT JOIN findings f ON f.chat_id = c.id
LEFT JOIN conversation_insights ci ON ci.chat_id = c.id;

-- 2. Findings by category + severity (for the leak breakdown charts)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_findings_by_category AS
SELECT
    f.category,
    f.severity,
    f.analyzer,
    c.provider,
    c.model_name,
    COUNT(*) AS finding_count
FROM findings f
JOIN chats c ON c.id = f.chat_id
GROUP BY f.category, f.severity, f.analyzer, c.provider, c.model_name
ORDER BY finding_count DESC;

-- 3. Provider flow (for sovereignty / data flow panel)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_provider_stats AS
SELECT
    c.provider,
    c.model_name,
    COUNT(*) AS message_count,
    COUNT(DISTINCT c.conversation_key) AS conversation_count,
    COUNT(DISTINCT f.id) FILTER (WHERE f.category = 'security_leak') AS security_leaks,
    COUNT(DISTINCT f.id) FILTER (WHERE f.category = 'content_leak') AS content_leaks,
    COUNT(DISTINCT f.id) FILTER (WHERE f.category = 'supply_chain') AS supply_chain_findings,
    COUNT(DISTINCT f.id) FILTER (WHERE f.category = 'usage_quality') AS trivial_usage,
    AVG(CASE WHEN f.analyzer = 'llm_complexity' THEN (f.meta->>'complexity_score')::float END) AS avg_complexity
FROM chats c
LEFT JOIN findings f ON f.chat_id = c.id
GROUP BY c.provider, c.model_name
ORDER BY message_count DESC;

-- 4. Severity timeline (for trend sparklines)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_findings_timeline AS
SELECT
    DATE(c.conversation_timestamp) AS day,
    f.category,
    f.severity,
    COUNT(*) AS finding_count
FROM findings f
JOIN chats c ON c.id = f.chat_id
WHERE c.conversation_timestamp IS NOT NULL
GROUP BY DATE(c.conversation_timestamp), f.category, f.severity
ORDER BY day DESC;

-- 5. Top findings (for alert feed / detail view)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_findings AS
SELECT
    f.id,
    f.analyzer,
    f.category,
    f.severity,
    f.title,
    f.detail,
    f.snippet,
    f.confidence,
    f.created_at,
    c.provider,
    c.model_name,
    c.conversation_title,
    c.author,
    c.conversation_timestamp
FROM findings f
JOIN chats c ON c.id = f.chat_id
WHERE f.severity IN ('critical', 'high')
ORDER BY f.created_at DESC
LIMIT 100;

-- 6. Scatter plot data (complexity vs leak count per conversation)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_scatter_complexity_leaks AS
SELECT
    c.conversation_key,
    c.provider,
    c.model_name,
    COUNT(DISTINCT c.id) AS message_count,
    AVG(CASE WHEN f.analyzer = 'llm_complexity' THEN (f.meta->>'complexity_score')::float END) AS avg_complexity,
    COUNT(DISTINCT f.id) FILTER (WHERE f.category IN ('security_leak', 'content_leak')) AS leak_count,
    SUM(LENGTH(c.user_text_clean)) AS total_chars
FROM chats c
LEFT JOIN findings f ON f.chat_id = c.id
GROUP BY c.conversation_key, c.provider, c.model_name
HAVING COUNT(DISTINCT c.id) > 1;

-- Unique indexes required for CONCURRENT refresh
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_overview ON mv_dashboard_overview (refreshed_at);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_findings_cat ON mv_findings_by_category (category, severity, analyzer, provider, model_name);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_provider ON mv_provider_stats (provider, model_name);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_timeline ON mv_findings_timeline (day, category, severity);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_top ON mv_top_findings (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_scatter ON mv_scatter_complexity_leaks (conversation_key, provider, model_name);

-- Refresh function (called by worker after analysis)
CREATE OR REPLACE FUNCTION refresh_dashboard_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_overview;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_findings_by_category;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_provider_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_findings_timeline;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_findings;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_scatter_complexity_leaks;
END;
$$ LANGUAGE plpgsql;
