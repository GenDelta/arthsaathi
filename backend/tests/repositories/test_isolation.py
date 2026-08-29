"""Cross-tenant isolation tests — Task 2.6 verification.

Proves that a CITIZEN user cannot access another CITIZEN's data through
the repository layer. Returns empty/404 — never leaks another user's rows.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.repositories.user import UserRepository


async def test_user_cannot_fetch_another_users_record(test_db_path: str) -> None:
    """User A's get_by_id call with User B's ID must return NotFoundError."""
    repo = UserRepository(database_path=test_db_path)

    # Create two independent users
    user_a = await repo.create_user(
        name="Anita Devi",
        phone_number="+919876543210",
        password_hash=hash_password("password_a"),
    )
    user_b = await repo.create_user(
        name="Ravi Kumar",
        phone_number="+919876543211",
        password_hash=hash_password("password_b"),
    )

    # User A should see their own record fine
    result = await repo.get_by_id(user_a.id, requesting_user_id=user_a.id)
    assert result.id == user_a.id

    # User A trying to access User B's record must raise NotFoundError (404)
    # — not AuthorizationError (403) — to avoid leaking existence.
    with pytest.raises(NotFoundError):
        await repo.get_by_id(user_b.id, requesting_user_id=user_a.id)


async def test_get_by_phone_does_not_return_inactive_users(test_db_path: str) -> None:
    """Deactivated accounts must not be retrievable by phone lookup."""
    repo = UserRepository(database_path=test_db_path)

    user = await repo.create_user(
        name="Ghost User",
        phone_number="+919000000001",
        password_hash=hash_password("pass"),
    )

    # Manually deactivate
    import aiosqlite

    async with aiosqlite.connect(test_db_path) as conn:
        await conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user.id,))
        await conn.commit()

    result = await repo.get_by_phone("+919000000001")
    assert result is None


async def test_system_get_by_id_not_found_raises(test_db_path: str) -> None:
    repo = UserRepository(database_path=test_db_path)
    with pytest.raises(NotFoundError):
        await repo.get_by_id_system("non-existent-uuid")
