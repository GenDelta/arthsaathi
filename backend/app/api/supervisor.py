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

from fastapi.responses import StreamingResponse

@router.post("/chat")
async def chat_with_supervisor(
    req: SupervisorRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context)  # noqa: B008
):
    """Unified entry point for the Multi-Agent Supervisor."""
    
    config = {"configurable": {"thread_id": ctx.user_id}}
    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "user_id": ctx.user_id,
        "profile_context": {},
        "intent": None,
        "extracted_transaction": None,
        "flagged_entities": [],
        "final_response": None
    }
    
    async def event_stream():
        try:
            # We iterate through the LangGraph execution steps
            async for step in supervisor_agent.astream(initial_state, config=config):
                # step is a dict like {'node_name': state_updates}
                for node_name, state_update in step.items():
                    # Send an event to the frontend showing which agent is spinning up
                    yield f"data: {json.dumps({'type': 'agent_activity', 'node': node_name})}\n\n"
                    
                    if "client_action" in state_update and state_update["client_action"]:
                        yield f"data: {json.dumps({'type': 'action', 'action': state_update['client_action']['type'], 'path': state_update['client_action'].get('path')})}\n\n"
                    
                    if state_update.get("extracted_transaction"):
                        yield f"data: {json.dumps({'type': 'action', 'action': 'transaction_logged'})}\n\n"
                        from app.api.guardian import run_background_guardian_checks
                        background_tasks.add_task(run_background_guardian_checks, ctx.user_id)
                    
                    # If this is the final guard node, we can output the final response
                    if node_name == "output_guard":
                        final_res = state_update.get("final_response")
                        if final_res:
                            yield f"data: {json.dumps({'type': 'final_response', 'response': final_res})}\n\n"
            
            # End of stream
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Supervisor error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'response': 'An error occurred.'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
