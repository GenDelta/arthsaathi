import logging
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.core.dependencies import TenantContext, get_tenant_context
from app.agents.supervisor.agent import supervisor_agent
from app.agents.supervisor.state import ArthSaathiState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supervisor", tags=["supervisor"])

class SupervisorRequest(BaseModel):
    message: str

class SupervisorResponse(BaseModel):
    intent: str
    response: str
    action_payload: dict | None = None

@router.post("/chat", response_model=SupervisorResponse)
async def chat_with_supervisor(
    req: SupervisorRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context)  # noqa: B008
) -> SupervisorResponse:
    """Unified entry point for the Multi-Agent Supervisor."""
    
    # Initialize the LangGraph state
    config = {"configurable": {"thread_id": ctx.user_id}}
    
    # We pass the input into the graph
    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "user_id": ctx.user_id,
        "profile_context": {},
        "intent": None,
        "extracted_transaction": None,
        "flagged_entities": [],
        "final_response": None
    }
    
    try:
        # Run the supervisor LangGraph
        final_state = await supervisor_agent.ainvoke(initial_state, config=config)
        
        # The agent graph should output a final response and the determined intent
        intent = final_state.get("intent", "GENERAL")
        response_text = final_state.get("final_response", "I'm not sure how to help with that.")
        
        # We can extract any action payload if a transaction was logged or entity flagged
        action_payload = {}
        if final_state.get("extracted_transaction"):
            action_payload["transaction"] = final_state["extracted_transaction"]
        if final_state.get("flagged_entities"):
            action_payload["flagged"] = final_state["flagged_entities"]
            
        return SupervisorResponse(
            intent=intent,
            response=response_text,
            action_payload=action_payload
        )
        
    except Exception as e:
        logger.error(f"Supervisor error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Supervisor agent encountered an error.")
