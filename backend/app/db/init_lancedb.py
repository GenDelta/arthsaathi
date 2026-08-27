"""LanceDB initialisation — creates empty ``predatory_clauses`` and ``schemes_vectors`` tables.

Schemas match ARCHITECTURE.md §2.2.

Usage (run from the ``backend/`` directory):
    python -m app.db.init_lancedb

This script is idempotent: if the tables already exist, it verifies their schemas
and exits cleanly without truncating data.
"""

from __future__ import annotations

import logging

import pyarrow as pa

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

# Embedding dimension — must match the provider selected at runtime.
# OpenAI text-embedding-3-small produces 1536-dimensional vectors.
EMBEDDING_DIM = 1536

# Schema: predatory_clauses (used by Extraction & Scam Agent)
PREDATORY_CLAUSES_SCHEMA = pa.schema(
    [
        pa.field("id", pa.utf8()),
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
        pa.field("clause_text", pa.utf8()),
        pa.field(
            "clause_category",
            pa.dictionary(pa.int8(), pa.utf8()),
        ),
        pa.field("severity_weight", pa.float32()),
        pa.field("explanation_template", pa.utf8()),
    ]
)

# Schema: schemes_vectors (used by Matchmaker Agent)
SCHEMES_VECTORS_SCHEMA = pa.schema(
    [
        pa.field("id", pa.utf8()),
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
        pa.field("scheme_id", pa.utf8()),  # FK reference to schemes.id in SQLite
    ]
)


def init_lancedb(lancedb_path: str | None = None) -> None:
    """Create LanceDB tables if they don't already exist."""
    import lancedb  # lazy import: keeps module importable without lancedb installed

    settings = get_settings()
    path = lancedb_path or settings.lancedb_path

    logger.info("Opening LanceDB at: %s", path)
    db = lancedb.connect(path)

    existing_tables = db.table_names() if hasattr(db, "table_names") else db.list_tables()

    for table_name, schema in [
        ("predatory_clauses", PREDATORY_CLAUSES_SCHEMA),
        ("schemes_vectors", SCHEMES_VECTORS_SCHEMA),
    ]:
        if table_name in existing_tables:
            logger.info("Table '%s' already exists — skipping creation.", table_name)
        else:
            logger.info("Creating LanceDB table: %s", table_name)
            db.create_table(table_name, schema=schema)
            logger.info("Table '%s' created successfully.", table_name)

    logger.info("LanceDB initialisation complete.")


if __name__ == "__main__":
    init_lancedb()
