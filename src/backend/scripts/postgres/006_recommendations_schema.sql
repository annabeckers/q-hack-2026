CREATE TABLE IF NOT EXISTS system_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    impact_score INTEGER NOT NULL CHECK (impact_score >= 0 AND impact_score <= 100),
    target_audience VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_status ON system_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_impact ON system_recommendations(impact_score);
