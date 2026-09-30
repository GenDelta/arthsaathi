import asyncio
import logging
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.onboarding.graph import build_onboarding_graph

logging.basicConfig(level=logging.INFO)

async def test():
    state = {
        "messages": [
            AIMessage(content="What type of work do you do—do you have a regular salary, work on a gig basis, or farm seasonally?"),
            HumanMessage(content="Farm seasonally"),
            AIMessage(content="Thanks for sharing that! On average, how much do you earn every season (in INR)?"),
            HumanMessage(content="2000")
        ],
        "current_profile": {},
        "language": "en"
    }
    
    agent = build_onboarding_graph()
    
    res = await agent.ainvoke(state)
    print("PROFILE AFTER 2000:", res.get("current_profile"))

    state["messages"].extend(res.get("messages", []))
    state["messages"].append(AIMessage(content="Got it! You earn around ₹2,000 each season, right?"))
    state["messages"].append(HumanMessage(content="yes"))
    state["current_profile"] = res.get("current_profile")
    
    res2 = await agent.ainvoke(state)
    print("PROFILE AFTER yes:", res2.get("current_profile"))

asyncio.run(test())
