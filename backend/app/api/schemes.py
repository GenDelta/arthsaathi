import logging
import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context
from app.agents.matchmaker.graph import matchmaker_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schemes", tags=["schemes"])

class MatchResponse(BaseModel):
    schemes: List[dict]

@router.post("/match", response_model=MatchResponse)
async def match_schemes(ctx: TenantContext = Depends(get_tenant_context)) -> MatchResponse:
    db_path = get_settings().database_path
    
    # Fetch user profile
    profile = {}
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (ctx.user_id,))
        row = await cursor.fetchone()
        if row:
            profile = dict(row)
            
    # Execute LangGraph workflow
    state = {
        "user_profile": profile,
        "behavioral_summary": "Standard risk profile.", # In phase 4, this comes from flagged_entities
        "central_candidates": [],
        "state_candidates": [],
        "final_schemes": []
    }
    
    result = await matchmaker_agent.ainvoke(state)
    
    return MatchResponse(schemes=result.get("final_schemes", []))

