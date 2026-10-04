"""LLM provider factory for ArthSaathi agents.

All four agents (Scam, Matchmaker, Storyteller, Guardian) call ``get_llm()``
rather than constructing a model directly. Swapping models is a single .env change.
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import get_settings


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """Return a configured LangChain chat model based on the active LLM provider."""
    settings = get_settings()

    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama  # type: ignore[import-untyped]
        return ChatOllama(
            model=settings.llm_model_name,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model_name,
            api_key=settings.llm_api_key,  # type: ignore[arg-type]
            base_url=settings.openai_api_base,
            temperature=temperature,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.llm_model_name,
            api_key=settings.llm_api_key,  # type: ignore[arg-type]
            temperature=temperature,
        )

    msg = f"Unknown LLM provider: {settings.llm_provider!r}"
    raise ValueError(msg)

from functools import lru_cache

@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """Return a configured LangChain Embeddings model based on the active provider.
    Currently forces local HuggingFace embeddings to save cloud quota.
    """
    settings = get_settings()

    try:
        from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore[import-untyped]
        return HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
    except ImportError:
        raise ValueError("Please install langchain-huggingface and sentence-transformers for embeddings") from None

