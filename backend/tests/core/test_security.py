"""Tests for app/core/security.py — Task 2.1 verification."""

from __future__ import annotations

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

# ─── Password hashing ─────────────────────────────────────────────────────────


def test_hash_password_produces_bcrypt_hash() -> None:
    hashed = hash_password("securepassword123")
    assert hashed.startswith("$2b$")


def test_verify_password_correct() -> None:
    hashed = hash_password("securepassword123")
    assert verify_password("securepassword123", hashed) is True


def test_verify_password_wrong() -> None:
    hashed = hash_password("securepassword123")
    assert verify_password("wrongpassword", hashed) is False


def test_hash_is_not_plaintext() -> None:
    plain = "mysecretpassword"
    assert hash_password(plain) != plain


# ─── Access token round-trip ──────────────────────────────────────────────────


def test_access_token_round_trip() -> None:
    """Encode an access token, decode it, assert claims match input."""
    user_id = "user-uuid-1234"
    role = "CITIZEN"
    org_id = None

    token = create_access_token(user_id, role, org_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["org_id"] == org_id
    assert payload["token_type"] == "access"  # noqa: S105
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_with_org() -> None:
    token = create_access_token("user-1", "NGO_ADMIN", "org-uuid-99")
    payload = decode_token(token)
    assert payload["org_id"] == "org-uuid-99"
    assert payload["role"] == "NGO_ADMIN"


# ─── Refresh token round-trip ─────────────────────────────────────────────────


def test_refresh_token_round_trip() -> None:
    user_id = "user-uuid-5678"
    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["token_type"] == "refresh"  # noqa: S105
    # Refresh token must NOT carry role or org (role changes take effect on next login)
    assert "role" not in payload
    assert "org_id" not in payload


# ─── Invalid / expired token handling ────────────────────────────────────────


def test_decode_garbage_token_raises() -> None:
    with pytest.raises(AuthenticationError):
        decode_token("this.is.garbage")


def test_decode_wrong_secret_raises() -> None:
    from datetime import UTC, datetime, timedelta

    import jwt as pyjwt

    bad_token = pyjwt.encode(
        {"sub": "x", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "wrong-secret",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        decode_token(bad_token)
