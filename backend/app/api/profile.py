import logging

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])

class ProfileResponse(BaseModel):
    id: str
    name: str
    phone_number: str
    language_pref: str
    employment_type: str | None = None
    occupation: str | None = None
    income_frequency: str | None = None
    average_income: float | None = None
    financial_pain_points: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    state_of_residence: str | None = None

@router.get("", response_model=ProfileResponse)
async def get_profile(ctx: TenantContext = Depends(get_tenant_context)) -> ProfileResponse:
    repo = UserRepository()
    user = await repo.get_by_id(ctx.user_id, ctx.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_path = get_settings().database_path
    
    # Fetch from user_profiles
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (ctx.user_id,)
        )
        profile_row = await cursor.fetchone()
        
    return ProfileResponse(
        id=user.id,
        name=user.name,
        phone_number=user.phone_number,
        language_pref=user.language_pref,
        employment_type=profile_row["employment_type"] if profile_row else None,
        occupation=profile_row["occupation"] if profile_row else None,
        income_frequency=profile_row["income_frequency"] if profile_row else None,
        average_income=profile_row["average_income"] if profile_row else None,
        financial_pain_points=profile_row["financial_pain_points"] if profile_row else None,
        date_of_birth=profile_row["date_of_birth"] if profile_row else None,
        gender=profile_row["gender"] if profile_row else None,
        state_of_residence=profile_row["state_of_residence"] if profile_row else None,
    )
