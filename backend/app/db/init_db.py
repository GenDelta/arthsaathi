"""Database initialisation script.

Applies all SQL migrations in ``app/db/migrations/`` in filename order,
then enables WAL mode and foreign-key enforcement.

Usage (run from the ``backend/`` directory):
    python -m app.db.init_db

The database file is created at the path specified by ``Settings.database_path``
(defaults to ``./arthsaathi.db``).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _get_connection(database_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(database_path)
    # Enable WAL mode for concurrent reads during writes (ARCHITECTURE.md §5.3)
    conn.execute("PRAGMA journal_mode=WAL;")
    # Enforce foreign-key constraints (SQLite does not do this by default)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply every *.sql file in the migrations directory, in sorted order."""
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        logger.warning("No migration files found in %s", MIGRATIONS_DIR)
        return

    for migration_path in migration_files:
        logger.info("Applying migration: %s", migration_path.name)
        sql = migration_path.read_text(encoding="utf-8")
        try:
            conn.executescript(sql)
        except sqlite3.OperationalError as exc:
            if "duplicate column name" in str(exc).lower():
                # Migration already partially applied (ALTER TABLE already ran).
                # Re-run only the non-ALTER statements using executescript on a
                # filtered version of the SQL.
                logger.debug("Duplicate column detected — skipping ALTER TABLE statements: %s", exc)
                filtered = "\n".join(
                    line for line in sql.splitlines()
                    if not line.strip().upper().startswith("ALTER TABLE")
                )
                conn.executescript(filtered)
            else:
                raise
        conn.commit()
        logger.info("Migration applied: %s", migration_path.name)


def init_db(database_path: str | None = None) -> str:
    """Initialise the SQLite database and return the path used.

    Args:
        database_path: Override the path from settings. Useful for tests.

    Returns:
        The absolute path to the database file that was initialised.
    """
    settings = get_settings()
    path = database_path or settings.database_path

    # Ensure parent directory exists
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initialising database at: %s", db_file.resolve())
    with _get_connection(str(db_file)) as conn:
        _apply_migrations(conn)

    logger.info("Database initialisation complete.")
    return str(db_file.resolve())


if __name__ == "__main__":
    init_db()
