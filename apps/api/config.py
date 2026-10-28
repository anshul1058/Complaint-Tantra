from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://anshul@127.0.0.1:5432/complaint_tantra"
    jwt_secret: str = "change-me-long-random-string"
    jwt_expiry_minutes: int = 720
    cors_origins: str = "http://localhost:3000"

    llm_provider: str = "none"
    llm_api_key: str = ""
    llm_model: str = ""
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"

    stuck_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
