"""UserRepository — all database access for the users table."""

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
    password_hash: str | None          # None for TOTP-only users
    occupation: str | None
    income_bracket: str | None
    language_pref: str
    role: str
    is_active: int
    is_onboarded: int
    totp_secret: str | None
    created_at: str
    updated_at: str


# ─── Repository ───────────────────────────────────────────────────────────────


class UserRepository:
    """Data-access layer for the ``users`` table."""

    def __init__(self, database_path: str | None = None) -> None:
        self._db_path = database_path or get_settings().database_path

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

    async def upsert_user_via_phone(self, phone_number: str) -> UserRow:
        """Fetch existing user by phone, or create a new one if not found.

        Used by the TOTP setup flow — no password required.
        New users are given a generated name (can be updated later in profile).
        """
        existing = await self.get_by_phone(phone_number)
        if existing:
            return existing

        # Generate a placeholder name from the last 4 digits
        last4 = phone_number[-4:]
        generated_name = f"User {last4}"

        user_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute(
                """
                INSERT INTO users
                    (id, name, phone_number, password_hash, language_pref, role, created_at, updated_at)
                VALUES (?, ?, ?, NULL, ?, ?, ?, ?)
                """,
                (user_id, generated_name, phone_number, "en", "CITIZEN", now, now),
            )
            await conn.commit()

        logger.info("Created new TOTP user id=%s phone=%s", user_id, phone_number)
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

    async def set_onboarded(self, user_id: str) -> None:
        """Mark a user as fully onboarded."""
        async with aiosqlite.connect(self._db_path) as conn:
            await conn.execute(
                "UPDATE users SET is_onboarded = 1, updated_at = datetime('now') WHERE id = ?",
                (user_id,),
            )
            await conn.commit()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _row_to_user(row: aiosqlite.Row) -> UserRow:
    keys = row.keys() if hasattr(row, "keys") else []
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
        is_onboarded=row["is_onboarded"] if "is_onboarded" in (row.keys() if hasattr(row, "keys") else []) else 0,
        totp_secret=row["totp_secret"] if "totp_secret" in (row.keys() if hasattr(row, "keys") else []) else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
