from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hackathon"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "hackathon"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8100

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # AI / Agent Config
    aws_region: str = "us-west-2"
    aws_bedrock_model_id: str = "us.anthropic.claude-sonnet-4-6"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Rust Worker
    rust_worker_url: str = "http://localhost:8080"

    # Security
    cors_origins: str = "*"  # comma-separated origins, or "*" for dev
    rate_limit_rpm: int = 120
    webhook_secret: str = ""

    # OpenTelemetry
    otel_enabled: bool = False  # explicit opt-in
    otel_service_name: str = "hackathon-backend"
    otel_exporter_endpoint: str = "http://localhost:4317"

    # Scheduler
    scheduler_enabled: bool = False  # explicit opt-in

    # App
    debug: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
