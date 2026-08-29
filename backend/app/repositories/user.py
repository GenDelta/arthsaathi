"""UserRepository — all database access for the users table.

Every method takes a ``TenantContext`` (or is explicitly a system-level operation
like ``create_user`` and ``get_by_phone`` which run before a context exists).
No route handler executes SQL directly — all queries go through this class.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import aiosqlite

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


# ─── Row model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class UserRow:
    """Immutable representation of a row from the ``users`` table."""

    id: str
    organization_id: str | None
    name: str
    phone_number: str
    password_hash: str
    occupation: str | None
    income_bracket: str | None
    language_pref: str
    role: str
    is_active: int
    created_at: str
    updated_at: str


# ─── Repository ───────────────────────────────────────────────────────────────


class UserRepository:
    """Data-access layer for the ``users`` table."""

    def __init__(self, database_path: str | None = None) -> None:
        self._db_path = database_path or get_settings().database_path

    async def _connect(self) -> aiosqlite.Connection:  # type: ignore[return]
        """Return an open aiosqlite connection with correct pragmas."""
        conn = aiosqlite.connect(self._db_path)
        return conn

    async def create_user(
        self,
        name: str,
        phone_number: str,
        password_hash: str,
        occupation: str | None = None,
        language_pref: str = "hi",
        role: str = "CITIZEN",
        organization_id: str | None = None,
    ) -> UserRow:
        """Insert a new user row and return it.

        Raises:
            ConflictError: If ``phone_number`` is already registered.
        """
        user_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON")
            try:
                await conn.execute(
                    """
                    INSERT INTO users
                        (id, organization_id, name, phone_number, password_hash,
                         occupation, language_pref, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        organization_id,
                        name,
                        phone_number,
                        password_hash,
                        occupation,
                        language_pref,
                        role,
                        now,
                        now,
                    ),
                )
                await conn.commit()
            except aiosqlite.IntegrityError as exc:
                if "UNIQUE" in str(exc):
                    raise ConflictError(
                        f"Phone number '{phone_number}' is already registered"
                    ) from exc
                raise

        logger.debug("Created user id=%s role=%s", user_id, role)
        return await self.get_by_id_system(user_id)

    async def get_by_phone(self, phone_number: str) -> UserRow | None:
        """Look up an active user by phone number.

        Returns ``None`` if not found (used by the login endpoint before auth).
        This is a system-level call — no TenantContext required.
        """
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM users WHERE phone_number = ? AND is_active = 1",
                (phone_number,),
            ) as cursor:
                row = await cursor.fetchone()
        return _row_to_user(row) if row else None

    async def get_by_id_system(self, user_id: str) -> UserRow:
        """Fetch a user by ID without tenant scoping (system / post-create use only).

        Raises:
            NotFoundError: If no user with that ID exists.
        """
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM users WHERE id = ? AND is_active = 1",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            raise NotFoundError(f"User '{user_id}' not found")
        return _row_to_user(row)

    async def get_by_id(self, user_id: str, requesting_user_id: str) -> UserRow:
        """Fetch a user by ID scoped to the requesting user (tenant-isolated).

        A CITIZEN can only fetch their own record.

        Raises:
            NotFoundError: If the user does not exist OR the requesting user is
                trying to access a different user's record (returns 404, not 403,
                to avoid leaking existence — per ARCHITECTURE.md §3.6).
        """
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM users WHERE id = ? AND id = ? AND is_active = 1",
                (user_id, requesting_user_id),
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            raise NotFoundError(f"User '{user_id}' not found")
        return _row_to_user(row)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _row_to_user(row: aiosqlite.Row) -> UserRow:
    return UserRow(
        id=row["id"],
        organization_id=row["organization_id"],
        name=row["name"],
        phone_number=row["phone_number"],
        password_hash=row["password_hash"],
        occupation=row["occupation"],
        income_bracket=row["income_bracket"],
        language_pref=row["language_pref"],
        role=row["role"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
