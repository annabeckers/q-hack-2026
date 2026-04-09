-- Popular packages table for slopsquatting detection

CREATE TABLE IF NOT EXISTS popular_packages (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    ecosystem VARCHAR(100) NOT NULL,
    downloads BIGINT DEFAULT 0,
    dependent_packages_count INTEGER DEFAULT 0,
    description TEXT,
    repository_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ecosystem, name)
);

CREATE INDEX IF NOT EXISTS ix_popular_packages_ecosystem ON popular_packages (ecosystem);
CREATE INDEX IF NOT EXISTS ix_popular_packages_name ON popular_packages (name);
