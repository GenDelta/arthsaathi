import asyncio
import logging
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.onboarding.graph import build_onboarding_graph

logging.basicConfig(level=logging.INFO)

async def test():
    state = {
        "messages": [
            AIMessage(content="How do you usually earn your income? (e.g., salary, gigs, seasonal farming, etc.)"),
            HumanMessage(content="Farming"),
            AIMessage(content="Is your farming work paid on a regular salary, as a self‑employed venture, or do you earn it seasonally?"),
            HumanMessage(content="Seasonally")
        ],
        "current_profile": {},
        "language": "en"
    }
    
    agent = build_onboarding_graph()
    res = await agent.ainvoke(state)
    print("PROFILE:", res.get("current_profile"))

asyncio.run(test())
