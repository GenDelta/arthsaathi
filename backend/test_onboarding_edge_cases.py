import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.onboarding.graph import onboarding_agent

async def simulate_persona(name, responses):
    print(f"\n--- Running Test for Persona: {name} ---")
    state = {
        "messages": [],
        "current_profile": {},
        "user_id": "test_user",
        "language": "en",
        "is_complete": False
    }
    
    # Kickoff
    res = await onboarding_agent.ainvoke(state)
    state["messages"].extend(res["messages"])
    print(f"AI: {state['messages'][-1].content}")
    
    turn = 0
    while not state.get("is_complete") and turn < len(responses):
        user_reply = responses[turn]
        print(f"User: {user_reply}")
        state["messages"].append(HumanMessage(content=user_reply))
        
        # Invoke agent
        res = await onboarding_agent.ainvoke(state)
        # Langgraph state merging returns full lists, we need to assign it back
        state["messages"] = res["messages"]
        state["current_profile"] = res.get("current_profile", state["current_profile"])
        state["is_complete"] = res.get("is_complete", False)
        
        print(f"AI: {state['messages'][-1].content}")
        print(f"[Extracted so far: {state['current_profile']}]")
        
        turn += 1
        
    if state["is_complete"]:
        print(f"✅ SUCCESS: {name} completed in {turn} turns.")
    else:
        print(f"❌ FAILED: {name} got stuck. Missing: {[f for f in ['name', 'date_of_birth', 'gender', 'state_of_residence', 'employment_type', 'occupation', 'income_frequency', 'average_income', 'financial_pain_points'] if f not in state['current_profile']]}")

async def run_tests():
    p1 = ["Raj", "25/08/90", "M", "UP", "Gig", "Uber", "daily", "500", "petrol cost"]
    await simulate_persona("Short Answers", p1)
    
    p2 = ["I am Sunita from a small village.", "I was born around Diwali in 1985.", "Female", "Currently living in Bihar.", "I work on other people's farms during the harvest season.", "Just manual farm labor.", "When the season ends.", "Maybe 10000 per season.", "Medical bills for my husband."]
    await simulate_persona("Over-Sharer", p2)

asyncio.run(run_tests())
