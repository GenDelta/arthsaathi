"""Security utilities: password hashing and JWT token management.

This module is the single source of truth for all cryptographic operations.
Route handlers never call jwt.encode/decode directly — they use these functions.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

_ACCESS_TOKEN_TYPE = "access"  # noqa: S105
_REFRESH_TOKEN_TYPE = "refresh"  # noqa: S105


# ─── Password hashing ─────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt (cost factor 12).

    Args:
        plain: The raw password string from the user.

    Returns:
        A bcrypt hash string suitable for storage.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a plain-text password against a stored bcrypt hash.

    Args:
        plain: The raw password string to verify.
        hashed: The stored bcrypt hash string.

    Returns:
        ``True`` if the password matches; ``False`` otherwise.
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ─── Token creation ───────────────────────────────────────────────────────────


def create_access_token(
    user_id: str,
    role: str,
    organization_id: str | None,
) -> str:
    """Issue a short-lived JWT access token.

    Claims follow ARCHITECTURE.md §3.1:
    ``{ sub, role, org_id, iat, exp, token_type }``.

    Args:
        user_id: The UUID of the authenticated user (``sub`` claim).
        role: The user's RBAC role string (e.g. ``"CITIZEN"``).
        organization_id: UUID of the user's organisation, or ``None`` for citizens.

    Returns:
        A signed JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "org_id": organization_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "token_type": _ACCESS_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """Issue a long-lived JWT refresh token.

    Only contains ``sub``, ``iat``, ``exp``, and ``token_type`` — no role/org
    so that role changes take effect on the next full login.

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        A signed JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_ttl_days),
        "token_type": _REFRESH_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# ─── Token decoding ───────────────────────────────────────────────────────────


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Validates signature, expiry, and algorithm.  Does NOT verify ``token_type``
    — callers are responsible for checking that field when it matters.

    Args:
        token: A raw JWT string (without ``Bearer `` prefix).

    Returns:
        The decoded payload dict.

    Raises:
        AuthenticationError: If the token is expired, malformed, or has an
            invalid signature.
    """
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        raise AuthenticationError("Token has expired") from None
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT invalid: %s", exc)
        raise AuthenticationError("Invalid token") from exc
