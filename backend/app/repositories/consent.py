"""ConsentRepository — data access for user_consents table."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
import aiosqlite
from app.core.config import get_settings

@dataclass
class ConsentRecord:
    purpose: str
    granted: bool
    notice_version: str
    updated_at: str

class ConsentRepository:
    def __init__(self, database_path: str | None = None) -> None:
        self._db_path = database_path or get_settings().database_path

    async def has_active_consent(self, user_id: str, purpose: str, notice_version: str) -> bool:
        async with aiosqlite.connect(self._db_path) as conn:
            cur = await conn.execute(
                """
                SELECT granted, notice_version 
                FROM user_consents 
                WHERE user_id = ? AND purpose = ? 
                ORDER BY created_at DESC 
                LIMIT 1
                """,
                (user_id, purpose)
            )
            row = await cur.fetchone()
            if not row:
                return False
            granted, version = row
            return bool(granted) and version == notice_version

    async def grant_consent(self, user_id: str, purpose: str, notice_version: str, method: str = 'UI') -> None:
        async with aiosqlite.connect(self._db_path) as conn:
            await conn.execute(
                """
                INSERT INTO user_consents (id, user_id, purpose, granted, notice_version, method, created_at)
                VALUES (?, ?, ?, 1, ?, ?, ?)
                """,
                (str(uuid.uuid4()), user_id, purpose, notice_version, method, datetime.now(UTC).isoformat())
            )
            await conn.commit()

    async def withdraw_consent(self, user_id: str, purpose: str, notice_version: str, method: str = 'UI') -> None:
        async with aiosqlite.connect(self._db_path) as conn:
            await conn.execute(
                """
                INSERT INTO user_consents (id, user_id, purpose, granted, notice_version, method, created_at)
                VALUES (?, ?, ?, 0, ?, ?, ?)
                """,
                (str(uuid.uuid4()), user_id, purpose, notice_version, method, datetime.now(UTC).isoformat())
            )
            await conn.commit()

    async def get_all_status(self, user_id: str) -> list[ConsentRecord]:
        async with aiosqlite.connect(self._db_path) as conn:
            cur = await conn.execute(
                """
                SELECT purpose, granted, notice_version, created_at
                FROM user_consents
                WHERE user_id = ?
                ORDER BY created_at ASC
                """,
                (user_id,)
            )
            # Latest status for each purpose
            latest = {}
            for row in await cur.fetchall():
                latest[row[0]] = ConsentRecord(
                    purpose=row[0],
                    granted=bool(row[1]),
                    notice_version=row[2],
                    updated_at=row[3]
                )
            return list(latest.values())

    async def erase_user_financial_data(self, user_id: str) -> dict[str, int]:
        counts = {}
        async with aiosqlite.connect(self._db_path) as conn:
            async def safe_delete(table):
                cur = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if await cur.fetchone():
                    cur = await conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                    counts[table] = cur.rowcount
                else:
                    counts[table] = 0

            await safe_delete("transactions")
            await safe_delete("tracked_debts")
            await safe_delete("savings_goals")
            await safe_delete("nudges")
            await safe_delete("guardian_nudges")
            await safe_delete("nudge_feedback")
            await safe_delete("flagged_entities")
            await safe_delete("documents")
            await safe_delete("account_bindings")
            
            cur = await conn.execute("DELETE FROM audit_logs WHERE actor_user_id = ? AND resource = 'transactions'", (user_id,))
            counts["audit_logs"] = cur.rowcount
            await conn.execute("DELETE FROM user_consents WHERE user_id = ?", (user_id,))
            await conn.commit()
            
        return counts
