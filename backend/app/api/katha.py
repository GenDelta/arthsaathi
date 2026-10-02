import json
import logging
from typing import AsyncGenerator

import aiosqlite
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context
from app.core.llm import get_llm
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/katha", tags=["katha"])


class KathaRequest(BaseModel):
    message: str


@router.post("/stream")
async def stream_katha(
    req: KathaRequest,
    ctx: TenantContext = Depends(get_tenant_context)  # noqa: B008
) -> StreamingResponse:
    """Stream a folklore-based financial explanation."""
    
    # Fetch User Profile Context
    repo = UserRepository()
    user = await repo.get_by_id(ctx.user_id, ctx.user_id)
    language = "en"
    if user:
        language = user.language_pref

    db_path = get_settings().database_path
    occupation = "worker"
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        c = await conn.execute("SELECT occupation FROM user_profiles WHERE user_id = ?", (ctx.user_id,))
        row = await c.fetchone()
        if row and row["occupation"]:
            occupation = row["occupation"]

    lang_map = {"en": "English", "hi": "Hindi"}
    target_language = lang_map.get(language, "English")

    system_prompt = f"""You are ArthSaathi's Katha Agent.
Your job is to explain complex financial concepts through relatable, hyper-local Indian folk stories or analogies.
The user's occupation is: {occupation}.
You MUST explain the concept using an analogy related to their occupation (e.g. if they are a farmer, use a farming analogy; if a driver, use a vehicle analogy).
CRITICAL RULE: The story MUST be strictly under 100 words. Be concise.
CRITICAL RULE: Respond exclusively in {target_language}."""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            llm = get_llm(temperature=0.7)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=req.message)
            ]
            
            async for chunk in llm.astream(messages):
                if chunk.content:
                    # Server-Sent Event formatting requires data: prefix and \n\n suffix
                    yield f"data: {json.dumps({'text': chunk.content})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Katha Stream Error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
