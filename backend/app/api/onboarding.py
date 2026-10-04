"""Onboarding API router."""

import logging

import aiosqlite
from fastapi import APIRouter, Depends, BackgroundTasks
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from app.agents.onboarding.graph import onboarding_agent
from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    current_profile: dict = {}

class ChatResponse(BaseModel):
    reply: str
    is_complete: bool
    current_profile: dict

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, ctx: TenantContext = Depends(get_tenant_context)) -> ChatResponse:
    messages = []
    if body.message.strip():
        messages.append(HumanMessage(content=body.message))
        
    state = {
        "messages": messages,
        "current_profile": body.current_profile,
        "user_id": ctx.user_id,
        "language": body.language,
        "is_complete": False
    }
    
    result = await onboarding_agent.ainvoke(state)
    
    reply = ""
    if result.get("messages") and isinstance(result["messages"][-1], AIMessage):
        reply = result["messages"][-1].content
        
    return ChatResponse(
        reply=reply,
        is_complete=result.get("is_complete", False),
        current_profile=result.get("current_profile", {})
    )

class CompleteRequest(BaseModel):
    profile: dict

class CompleteResponse(BaseModel):
    success: bool

@router.post("/complete", response_model=CompleteResponse)
async def complete_onboarding(body: CompleteRequest, background_tasks: BackgroundTasks, ctx: TenantContext = Depends(get_tenant_context)) -> CompleteResponse:
    db_path = get_settings().database_path
    profile = body.profile

    # --- Sanitize enum values against DB CHECK constraints ---
    VALID_EMPLOYMENT_TYPES = {"SALARIED", "GIG_WORKER", "SEASONAL", "UNEMPLOYED"}
    VALID_INCOME_FREQUENCIES = {"DAILY", "WEEKLY", "MONTHLY", "SEASONAL"}

    raw_emp = (profile.get("employment_type") or "").upper().strip()
    # Normalise common LLM variants
    emp_map = {
        "GIG": "GIG_WORKER", "FREELANCE": "GIG_WORKER", "SELF_EMPLOYED": "GIG_WORKER",
        "PART_TIME": "SALARIED", "FULL_TIME": "SALARIED",
        "AGRICULTURAL": "SEASONAL", "FARMING": "SEASONAL",
        "DAILY_WAGE": "SALARIED", "DAILY WAGE": "SALARIED",
    }
    raw_emp = emp_map.get(raw_emp, raw_emp)
    employment_type = raw_emp if raw_emp in VALID_EMPLOYMENT_TYPES else None

    raw_freq = (profile.get("income_frequency") or "").upper().strip()
    freq_map = {"IRREGULAR": "SEASONAL", "FORTNIGHTLY": "WEEKLY", "ANNUALLY": "SEASONAL", "YEARLY": "SEASONAL"}
    raw_freq = freq_map.get(raw_freq, raw_freq)
    income_frequency = raw_freq if raw_freq in VALID_INCOME_FREQUENCIES else None

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """
            INSERT INTO user_profiles 
                (user_id, employment_type, occupation, income_frequency, average_income, financial_pain_points, date_of_birth, gender, state_of_residence, legal_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                employment_type = excluded.employment_type,
                occupation = excluded.occupation,
                income_frequency = excluded.income_frequency,
                average_income = excluded.average_income,
                financial_pain_points = excluded.financial_pain_points,
                date_of_birth = excluded.date_of_birth,
                gender = excluded.gender,
                state_of_residence = excluded.state_of_residence,
                legal_name = excluded.legal_name,
                updated_at = datetime('now')
            """,
            (
                ctx.user_id,
                employment_type,
                profile.get("occupation"),
                income_frequency,
                profile.get("average_income"),
                profile.get("financial_pain_points"),
                profile.get("date_of_birth"),
                profile.get("gender"),
                profile.get("state_of_residence"),
                profile.get("legal_name")
            )
        )

        # Update name and onboarding flag in users table
        name = profile.get("name")
        if name:
            await conn.execute("UPDATE users SET is_onboarded = 1, name = ? WHERE id = ?", (name, ctx.user_id))
        else:
            await conn.execute("UPDATE users SET is_onboarded = 1 WHERE id = ?", (ctx.user_id,))

        await conn.commit()
        logger.info("Onboarding complete for user %s (employment=%s freq=%s)", ctx.user_id, employment_type, income_frequency)

    # Queue background calculation of scheme matches
    from app.services.scheme_cacher import compute_and_cache_schemes
    background_tasks.add_task(compute_and_cache_schemes, ctx.user_id, profile)

    return CompleteResponse(success=True)
