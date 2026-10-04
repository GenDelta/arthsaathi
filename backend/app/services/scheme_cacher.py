import asyncio
import json
import logging
import aiosqlite
from app.core.config import get_settings
from app.agents.matchmaker.graph import matchmaker_agent

logger = logging.getLogger(__name__)

async def compute_and_cache_schemes(user_id: str, profile: dict):
    logger.info(f"Background task starting: computing scheme matches for user {user_id}")
    try:
        state = {
            "user_profile": profile,
            "behavioral_summary": "Standard risk profile.",
            "query": "",
            "central_candidates": [],
            "state_candidates": [],
            "final_schemes": []
        }
        result = await matchmaker_agent.ainvoke(state)
        final_schemes = result.get("final_schemes", [])
        
        db_path = get_settings().database_path
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                "UPDATE user_profiles SET cached_schemes = ? WHERE user_id = ?",
                (json.dumps(final_schemes), user_id)
            )
            await conn.commit()
        logger.info(f"Background task finished: cached {len(final_schemes)} schemes for user {user_id}")
    except Exception as e:
        logger.error(f"Background task failed for user {user_id}: {e}")

