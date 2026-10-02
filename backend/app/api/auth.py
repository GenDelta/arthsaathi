"""Authentication endpoints: register, login, refresh, /me, and TOTP setup/verify.

Implements ARCHITECTURE.md §3.1.  Route handlers raise domain exceptions
(AuthenticationError, ConflictError) — they do NOT construct HTTPException
directly.  The exception handler in app/main.py maps these to HTTP responses.

TOTP Auth Flow:
  POST /api/auth/totp/setup   → New user provides phone → get secret + QR code URI
  POST /api/auth/totp/verify  → User provides phone + 6-digit TOTP code → get JWT
"""

from __future__ import annotations

import base64
import io
import logging

import aiosqlite
import pyotp
import qrcode
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Request / Response models ────────────────────────────────────────────────



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
    is_onboarded: bool


# ─── TOTP Models ──────────────────────────────────────────────────────────────


class TotpSetupRequest(BaseModel):
    """Provide a phone number to get a TOTP setup QR code."""
    phone_number: str = Field(..., pattern=r"^\+91\d{10}$")
    force_reset: bool = False


class TotpSetupResponse(BaseModel):
    """
    Returns:
      - qr_code_uri: a data: URI (base64 PNG) of the QR code to scan.
      - secret: the raw base32 secret (for manual entry in authenticator apps).
      - is_new_user: True if this is first-time setup, False if secret already exists.
    """
    qr_code_uri: str
    secret: str
    is_new_user: bool


class TotpVerifyRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+91\d{10}$")
    totp_code: str = Field(..., min_length=6, max_length=6)


class TotpVerifyResponse(BaseModel):
    access_token: str
    refresh_token: str
    is_onboarded: bool


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(body: RefreshRequest) -> RefreshResponse:
    """Exchange a valid refresh token for a new access token."""
    payload = decode_token(body.refresh_token)

    if payload.get("token_type") != "refresh":
        raise AuthenticationError("Provided token is not a refresh token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing subject claim")

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
        is_onboarded=bool(user.is_onboarded),
    )


# ─── TOTP Endpoints ───────────────────────────────────────────────────────────


@router.post("/totp/setup", response_model=TotpSetupResponse)
async def totp_setup(body: TotpSetupRequest) -> TotpSetupResponse:
    """Step 1 of TOTP auth: upsert user, generate/return TOTP secret + QR code.

    - First call: generates a new TOTP secret for this phone number, stores it,
      and returns the QR code URI to scan with Google Authenticator / Authy.
    - Subsequent calls (user lost their secret): regenerates a fresh secret.
      The user must re-scan the QR code in their authenticator app.
    """
    db_path = get_settings().database_path
    repo = UserRepository()

    # Upsert the user (create if new, fetch if existing)
    user = await repo.upsert_user_via_phone(body.phone_number)

    is_new_user = not user.totp_secret or body.force_reset

    if is_new_user:
        # Generate a fresh TOTP secret for new users
        secret = pyotp.random_base32()
        
        # Persist the new secret
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                "UPDATE users SET totp_secret = ?, updated_at = datetime('now') WHERE id = ?",
                (secret, user.id),
            )
            await conn.commit()
        logger.info("New TOTP secret generated for user %s", user.id)
    else:
        # Returning user: reuse their existing secret!
        secret = user.totp_secret
        logger.info("Reusing existing TOTP secret for user %s", user.id)

    # Build the OTPAuth URI (compatible with Google Authenticator, Authy, etc.)
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=body.phone_number,
        issuer_name="ArthSaathi",
    )

    # Generate QR code as a base64 data URI so the frontend can embed it directly
    qr = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    qr_data_uri = f"data:image/png;base64,{qr_b64}"

    logger.info("TOTP secret generated for user %s (new=%s)", user.id, is_new_user)

    return TotpSetupResponse(
        qr_code_uri=qr_data_uri,
        secret=secret,
        is_new_user=is_new_user,
    )


@router.post("/totp/verify", response_model=TotpVerifyResponse)
async def totp_verify(body: TotpVerifyRequest) -> TotpVerifyResponse:
    """Step 2 of TOTP auth: verify the 6-digit code from the authenticator app.

    Validates with a ±1 window (30-second grace period for clock drift).

    Raises:
        AuthenticationError (401): If phone is not found, TOTP not set up,
            or the code is incorrect.
    """
    repo = UserRepository()
    user = await repo.get_by_phone(body.phone_number)

    if user is None:
        raise AuthenticationError("Phone number not registered. Please set up your authenticator first.")

    if not user.totp_secret:
        raise AuthenticationError("TOTP not configured. Please complete authenticator setup.")

    totp = pyotp.TOTP(user.totp_secret)

    # valid_window=1 allows the previous and next 30-second codes to handle clock drift
    if not totp.verify(body.totp_code, valid_window=1):
        raise AuthenticationError("Invalid or expired authenticator code. Try again.")

    logger.info("TOTP verified for user %s", user.id)
    return TotpVerifyResponse(
        access_token=create_access_token(user.id, user.role, user.organization_id),
        refresh_token=create_refresh_token(user.id),
        is_onboarded=bool(user.is_onboarded),
    )
