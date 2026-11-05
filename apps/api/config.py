from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parent
# Locally this module lives at <repo>/apps/api; in the Docker image the
# apps/api directory is copied directly to /app.
REPO_ROOT = CONFIG_DIR.parent.parent if CONFIG_DIR.parent.name == "apps" else CONFIG_DIR

# Agents (LiteLLM, Tavily) read os.getenv directly; make .env visible to them too.
load_dotenv(REPO_ROOT / ".env", override=False)


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
    embedding_model: str = "BAAI/bge-m3"

    stuck_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
