from pydantic_settings import BaseSettings


class DataloaderSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hackathon"
    chroma_host: str = "localhost"
    chroma_port: int = 8100
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "hackathon"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = DataloaderSettings()
