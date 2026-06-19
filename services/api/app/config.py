"""Application configuration.

All runtime config comes from environment variables, loaded (for local dev)
from the repo-root `.env`. In production you set real env vars and there is no
.env file — pydantic-settings handles both transparently.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> app -> api -> services -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # Ignore the many non-API vars in the shared root .env (POSTGRES_*, etc.).
        extra="ignore",
    )

    # SQLAlchemy connection URL, e.g.
    # postgresql+psycopg://mosaic:mosaic@localhost:5432/mosaic
    database_url: str = "postgresql+psycopg://mosaic:mosaic@localhost:5432/mosaic"

    # Browser origins allowed to call the API. Comma-separated in the env var.
    cors_origins: str = "http://localhost:3000"

    # Contact string SEC EDGAR requires as the User-Agent on every request.
    # Format: "AppName purpose your-email@example.com". SEC blocks requests
    # without a real contact. Set in .env; placeholder is rejected at runtime.
    sec_user_agent: str = "Mosaic research you@example.com"

    # Local sentence-transformers model for chunk + query embeddings (Milestone
    # 3). 384-dim; locked into migration 0004 — don't change without a re-embed.
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # LLM for grounded answers (Milestone 3). Provider is swappable behind the
    # app/llm seam. `mock` is a deterministic offline provider for tests.
    # `gemini` needs GEMINI_API_KEY (free from Google AI Studio).
    llm_provider: str = "gemini"
    # gemini-2.5-flash-lite is what this project's key actually serves (the older
    # gemini-2.0-flash returns limit:0 here). Swap via LLM_MODEL; free tier is
    # ~20 req/day/model, so answer_cache matters.
    llm_model: str = "gemini-2.5-flash-lite"
    gemini_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env is read once per process."""
    return Settings()
