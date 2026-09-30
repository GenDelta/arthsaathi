import json
import logging
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.core.llm import get_llm
from app.agents.supervisor.state import ArthSaathiState

logger = logging.getLogger(__name__)

# ─── Prompts ──────────────────────────────────────────────────────────────────

ROUTER_PROMPT = """You are the ArthSaathi Supervisor Router.
Your job is to analyze the user's input and classify their INTENT into exactly ONE of the following categories:

1. TRANSACTION: The user is reporting an income earned or an expense spent (e.g. "I got 500 from delivery", "paid 200 for food").
2. KATHA: The user is asking to explain a financial concept (e.g. "What is compound interest?").
3. SCHEME: The user is asking about welfare schemes, benefits, or government subsidies.
4. SCAM: The user is reporting a suspicious message, asking if a loan app is fake, or uploading contract text.
5. GENERAL: General conversation or questions that do not fit the above.

Output ONLY a JSON object with the key "intent" and the exact string value of the category.
Example: {{"intent": "TRANSACTION"}}"""

GUARD_PROMPT = """You are the ArthSaathi Adversarial Output Guard.
Review the proposed response to the user.
1. Ensure no guaranteed financial returns are promised.
2. Ensure there is no formal financial advisory phrasing.
3. Keep the tone helpful, empathetic, and simple.
If the response violates safety rules, output a safe, generalized fallback response instead.
Otherwise, output the response exactly as it is."""

# ─── Nodes ────────────────────────────────────────────────────────────────────

async def router_node(state: ArthSaathiState) -> dict:
    """Analyze the last message and route to the correct sub-agent."""
    llm = get_llm(temperature=0)
    last_msg = state["messages"][-1].content
    
    response = await llm.ainvoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=last_msg)
    ])
    
    raw = response.content.strip()
    if raw.startswith("```"):
        import re
        raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
        
    try:
        data = json.loads(raw)
        intent = data.get("intent", "GENERAL")
    except Exception:
        intent = "GENERAL"
        
    logger.info(f"Supervisor routed intent: {intent}")
    return {"intent": intent}


async def transaction_agent_node(state: ArthSaathiState) -> dict:
    """Node for Transaction extraction."""
    from app.api.transactions import _VOICE_EXTRACTION_PROMPT, _normalise_category, _ensure_transactions_table
    from app.core.config import get_settings
    import aiosqlite
    import uuid
    import re
    from datetime import datetime, timezone
    
    last_msg = state["messages"][-1].content
    user_id = state["user_id"]
    llm = get_llm(temperature=0.0)
    prompt = _VOICE_EXTRACTION_PROMPT.format(text=last_msg)
    
    try:
        response = await llm.ainvoke(prompt)
        raw_json = response.content.strip()
        if raw_json.startswith("```"):
            raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json).rstrip("`").strip()
            
        extracted = json.loads(raw_json)
        tx_type = str(extracted.get("type", "EXPENSE")).upper()
        if tx_type not in {"INCOME", "EXPENSE"}:
            tx_type = "EXPENSE"
            
        amount = float(extracted.get("amount", 0))
        if amount <= 0:
            return {"final_response": "I couldn't detect a valid amount. Please specify the amount clearly."}
            
        description = str(extracted.get("description", last_msg))[:500]
        category = _normalise_category(str(extracted.get("category", "OTHER")), tx_type)
        
        db_path = get_settings().database_path
        now = datetime.now(timezone.utc).isoformat()
        tx_id = str(uuid.uuid4())
        
        async with aiosqlite.connect(db_path) as conn:
            await _ensure_transactions_table(conn)
            await conn.execute(
                """
                INSERT INTO transactions
                    (id, user_id, type, category, amount, currency, description, occurred_at, created_at)
                VALUES (?, ?, ?, ?, ?, 'INR', ?, ?, ?)
                """,
                (tx_id, user_id, tx_type, category, amount, description, now, now),
            )
            await conn.commit()
            
        # We trigger the background rules via API wrapper or just return success
        # The background tasks are tied to FastAPI background_tasks, so we'll need to trigger them manually if we want
        return {
            "final_response": f"I have logged your {tx_type.lower()} of ₹{amount} for '{description}'.",
            "extracted_transaction": {"id": tx_id, "amount": amount, "type": tx_type}
        }
        
    except Exception as e:
        logger.error(f"Transaction extraction failed: {e}")
        return {"final_response": "I couldn't process that transaction right now. Please try again."}

import urllib.parse

async def katha_agent_node(state: ArthSaathiState) -> dict:
    """Mock node for Katha Mode routing."""
    last_msg = state["messages"][-1].content
    return {
        "final_response": "Redirecting you to Katha Mode for a story on that.",
        "client_action": {"type": "navigate", "path": f"/katha?q={urllib.parse.quote(last_msg)}"}
    }

async def scheme_agent_node(state: ArthSaathiState) -> dict:
    """Mock node for Matchmaker routing."""
    last_msg = state["messages"][-1].content
    return {
        "final_response": "Let me check the welfare schemes you qualify for.",
        "client_action": {"type": "navigate", "path": f"/schemes?q={urllib.parse.quote(last_msg)}"}
    }

async def scam_agent_node(state: ArthSaathiState) -> dict:
    """Mock node for Scam Scanner routing."""
    last_msg = state["messages"][-1].content
    return {
        "final_response": "I will redirect you to the Scam Scanner.",
        "client_action": {"type": "navigate", "path": f"/scam-scanner?q={urllib.parse.quote(last_msg)}"}
    }

async def general_agent_node(state: ArthSaathiState) -> dict:
    """Handle general chitchat."""
    llm = get_llm(temperature=0.6)
    sys_msg = "You are ArthSaathi, a friendly financial assistant for Indian gig workers."
    res = await llm.ainvoke([SystemMessage(content=sys_msg)] + list(state["messages"]))
    return {"final_response": res.content}


async def output_guard_node(state: ArthSaathiState) -> dict:
    """Validate final response for financial safety compliance."""
    llm = get_llm(temperature=0)
    proposed = state.get("final_response", "I cannot help with that right now.")
    
    res = await llm.ainvoke([
        SystemMessage(content=GUARD_PROMPT),
        HumanMessage(content=f"Proposed response:\n{proposed}")
    ])
    
    return {"final_response": res.content}

# ─── Edges ────────────────────────────────────────────────────────────────────

def route_intent(state: ArthSaathiState) -> Literal["transaction", "katha", "scheme", "scam", "general"]:
    intent = state.get("intent")
    if intent == "TRANSACTION": return "transaction"
    if intent == "KATHA": return "katha"
    if intent == "SCHEME": return "scheme"
    if intent == "SCAM": return "scam"
    return "general"

# ─── Graph Compilation ────────────────────────────────────────────────────────

def create_supervisor_graph():
    builder = StateGraph(ArthSaathiState)
    
    builder.add_node("router", router_node)
    builder.add_node("transaction", transaction_agent_node)
    builder.add_node("katha", katha_agent_node)
    builder.add_node("scheme", scheme_agent_node)
    builder.add_node("scam", scam_agent_node)
    builder.add_node("general", general_agent_node)
    builder.add_node("output_guard", output_guard_node)
    
    builder.set_entry_point("router")
    
    builder.add_conditional_edges(
        "router",
        route_intent,
        {
            "transaction": "transaction",
            "katha": "katha",
            "scheme": "scheme",
            "scam": "scam",
            "general": "general"
        }
    )
    
    # All sub-agents route to output guard before returning to user
    for node in ["transaction", "katha", "scheme", "scam", "general"]:
        builder.add_edge(node, "output_guard")
        
    builder.add_edge("output_guard", END)
    
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

supervisor_agent = create_supervisor_graph()
