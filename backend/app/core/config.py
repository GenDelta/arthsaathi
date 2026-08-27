"""Application settings loaded from environment variables / .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ─── JWT ──────────────────────────────────────────────────────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 7

    # ─── LLM provider ─────────────────────────────────────────────────────────
    llm_provider: str = "openai"  # "openai" | "anthropic"
    llm_api_key: str

    # ─── Database ─────────────────────────────────────────────────────────────
    database_path: str = "./arthsaathi.db"
    lancedb_path: str = "./.lancedb"

    # ─── Tesseract ────────────────────────────────────────────────────────────
    tesseract_cmd: str | None = None  # override if not on PATH

    # ─── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        if v not in {"openai", "anthropic"}:
            raise ValueError("llm_provider must be 'openai' or 'anthropic'")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]
