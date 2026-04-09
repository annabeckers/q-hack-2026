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

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Model Provider — switch between gemini, ollama, openai
    model_provider: str = "gemini"

    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite-preview"

    # Ollama (local models)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # OpenAI (optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Security
    cors_origins: str = "*"
    rate_limit_rpm: int = 120

    # Data
    data_root: str = "/data"

    # App
    debug: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
