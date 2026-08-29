"""FastAPI dependencies for authentication and role-based access control.

Every protected route must declare ``get_tenant_context`` as a dependency.
This is the single enforcement point for tenant isolation (ARCHITECTURE.md §1.4).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


# ─── TenantContext ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Decoded, validated identity of the requesting user.

    Injected by ``get_tenant_context`` into every authenticated route handler.
    Repository methods accept this as their first argument and apply the
    correct ``WHERE`` scoping internally.
    """

    user_id: str
    role: str
    organization_id: str | None


# ─── Dependencies ─────────────────────────────────────────────────────────────


async def get_tenant_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
) -> TenantContext:
    """Decode the Bearer token and return a ``TenantContext``.

    Raises:
        AuthenticationError: If the ``Authorization`` header is missing, the
            token is expired, or its signature is invalid.
    """
    if credentials is None:
        raise AuthenticationError("Missing authorization header")

    payload = decode_token(credentials.credentials)

    user_id: str | None = payload.get("sub")
    role: str | None = payload.get("role")

    if not user_id or not role:
        raise AuthenticationError("Token is missing required claims")

    logger.debug("Authenticated user_id=%s role=%s", user_id, role)

    return TenantContext(
        user_id=user_id,
        role=role,
        organization_id=payload.get("org_id"),
    )


def require_role(*roles: str) -> Callable[..., TenantContext]:
    """Dependency factory that gates a route to specific roles.

    Usage::

        @router.get("/ngo/dashboard")
        async def dashboard(ctx: TenantContext = Depends(require_role("NGO_ADMIN"))):
            ...

    Args:
        *roles: One or more allowed role strings (e.g. ``"NGO_ADMIN"``).

    Returns:
        A FastAPI dependency that resolves to the ``TenantContext`` if the
        role check passes, otherwise raises ``AuthorizationError`` (403).
    """
    allowed = frozenset(roles)

    async def _check(
        ctx: TenantContext = Depends(get_tenant_context),  # noqa: B008
    ) -> TenantContext:
        if ctx.role not in allowed:
            logger.warning(
                "Role check failed: user=%s role=%s required_one_of=%s",
                ctx.user_id,
                ctx.role,
                allowed,
            )
            raise AuthorizationError(f"Role '{ctx.role}' is not authorised for this resource")
        return ctx

    return _check
