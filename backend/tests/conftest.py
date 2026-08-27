"""Shared pytest fixtures for ArthSaathi backend tests.

Fixtures provided:
- ``test_db_path`` — a temporary SQLite DB path (initialised with migrations)
- ``async_client`` — an AsyncClient pointed at the FastAPI app with a test DB
- ``mock_llm`` — a patched LLM that returns a fixed response without API calls
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.init_db import init_db
from app.main import app


@pytest.fixture()
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary SQLite DB, apply migrations, yield the path, then delete."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        init_db(database_path=path)
        yield path
    finally:
        Path(path).unlink(missing_ok=True)


@pytest_asyncio.fixture()
async def async_client(test_db_path: str) -> AsyncGenerator[AsyncClient, None]:
    """Return an AsyncClient with the test database wired in via env override."""
    os.environ["DATABASE_PATH"] = test_db_path
    # Clear the Settings cache so the new DATABASE_PATH is picked up
    from app.core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Restore
    os.environ.pop("DATABASE_PATH", None)
    get_settings.cache_clear()  # type: ignore[attr-defined]
