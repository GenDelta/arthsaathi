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
    llm_provider: str = "ollama"  # "ollama" | "openai" | "anthropic"
    llm_api_key: str = "not-required-for-ollama"  # only used for openai/anthropic
    llm_model_name: str = "glm-5.3-flash"
    openai_api_base: str | None = None
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ─── Ollama ───────────────────────────────────────────────────────────────
    ollama_base_url: str = "http://127.0.0.1:11434"

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
        if v not in {"ollama", "openai", "anthropic"}:
            raise ValueError("llm_provider must be 'ollama', 'openai', or 'anthropic'")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]
