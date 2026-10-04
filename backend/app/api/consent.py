"""Consent API router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.consent import CURRENT_NOTICE_VERSION
from app.core.dependencies import TenantContext, get_tenant_context
from app.repositories.consent import ConsentRepository

router = APIRouter(prefix="/consent", tags=["consent"])

class GrantRequest(BaseModel):
    purposes: list[str]
    
class WithdrawRequest(BaseModel):
    purpose: str

class ConsentStatus(BaseModel):
    purpose: str
    granted: bool
    notice_version: str
    updated_at: str

class ConsentStatusResponse(BaseModel):
    consents: list[ConsentStatus]

class EraseResponse(BaseModel):
    erased_tables: dict[str, int]


@router.post("/grant")
async def grant_consent(
    body: GrantRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict[str, bool]:
    repo = ConsentRepository()
    for purpose in body.purposes:
        await repo.grant_consent(
            user_id=ctx.user_id,
            purpose=purpose,
            notice_version=CURRENT_NOTICE_VERSION,
            method="API"
        )
    return {"success": True}


@router.post("/withdraw")
async def withdraw_consent(
    body: WithdrawRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict[str, bool]:
    repo = ConsentRepository()
    await repo.withdraw_consent(
        user_id=ctx.user_id,
        purpose=body.purpose,
        notice_version=CURRENT_NOTICE_VERSION,
        method="API"
    )
    return {"success": True}


@router.get("/status", response_model=ConsentStatusResponse)
async def get_consent_status(
    ctx: TenantContext = Depends(get_tenant_context),
) -> ConsentStatusResponse:
    repo = ConsentRepository()
    records = await repo.get_all_status(ctx.user_id)
    return ConsentStatusResponse(
        consents=[
            ConsentStatus(
                purpose=r.purpose,
                granted=r.granted,
                notice_version=r.notice_version,
                updated_at=r.updated_at
            ) for r in records
        ]
    )


@router.delete("/erase", response_model=EraseResponse)
async def erase_financial_data(
    ctx: TenantContext = Depends(get_tenant_context),
) -> EraseResponse:
    repo = ConsentRepository()
    counts = await repo.erase_user_financial_data(ctx.user_id)
    return EraseResponse(erased_tables=counts)
