"""Authentication endpoints: register, login, refresh, and /me.

Implements ARCHITECTURE.md §3.1.  Route handlers raise domain exceptions
(AuthenticationError, ConflictError) — they do NOT construct HTTPException
directly.  The exception handler in app/main.py maps these to HTTP responses.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import TenantContext, get_tenant_context
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Request / Response models ────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone_number: str = Field(..., pattern=r"^\+91\d{10}$")
    password: str = Field(..., min_length=8, max_length=128)
    occupation: str | None = Field(None, max_length=100)
    language_pref: str = Field("hi", pattern=r"^[a-z]{2}$")


class RegisterResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    phone_number: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str


class MeResponse(BaseModel):
    id: str
    name: str
    role: str
    language_pref: str
    organization_id: str | None


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(body: RegisterRequest) -> RegisterResponse:
    """Register a new citizen account.

    Raises:
        ConflictError (409): If ``phone_number`` is already registered.
    """
    repo = UserRepository()
    hashed = hash_password(body.password)

    user = await repo.create_user(
        name=body.name,
        phone_number=body.phone_number,
        password_hash=hashed,
        occupation=body.occupation,
        language_pref=body.language_pref,
    )

    logger.debug("Registered new user id=%s", user.id)
    return RegisterResponse(
        user_id=user.id,
        access_token=create_access_token(user.id, user.role, user.organization_id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    """Authenticate with phone number and password.

    Raises:
        AuthenticationError (401): If the phone number is not found or the
            password is incorrect.  Both cases return the same error message
            to avoid user enumeration.
    """
    repo = UserRepository()
    user = await repo.get_by_phone(body.phone_number)

    if user is None or not verify_password(body.password, user.password_hash):
        raise AuthenticationError("Invalid phone number or password")

    logger.debug("User logged in id=%s role=%s", user.id, user.role)
    return LoginResponse(
        access_token=create_access_token(user.id, user.role, user.organization_id),
        refresh_token=create_refresh_token(user.id),
        role=user.role,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(body: RefreshRequest) -> RefreshResponse:
    """Exchange a valid refresh token for a new access token.

    Raises:
        AuthenticationError (401): If the refresh token is expired or invalid,
            or if it is not a refresh-type token.
    """
    payload = decode_token(body.refresh_token)

    if payload.get("token_type") != "refresh":
        raise AuthenticationError("Provided token is not a refresh token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing subject claim")

    # Re-fetch user to pick up any role/org changes since last login
    repo = UserRepository()
    user = await repo.get_by_id_system(user_id)

    return RefreshResponse(
        access_token=create_access_token(user.id, user.role, user.organization_id),
    )


@router.get("/me", response_model=MeResponse)
async def me(ctx: TenantContext = Depends(get_tenant_context)) -> MeResponse:  # noqa: B008
    """Return the profile of the currently authenticated user."""
    repo = UserRepository()
    user = await repo.get_by_id(ctx.user_id, ctx.user_id)

    return MeResponse(
        id=user.id,
        name=user.name,
        role=user.role,
        language_pref=user.language_pref,
        organization_id=user.organization_id,
    )
