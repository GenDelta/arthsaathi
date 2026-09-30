import asyncio
import json
from app.agents.matchmaker.graph import matchmaker_agent

async def run():
    state = {
        "user_profile": {
    "name":  "Test User",
    "date_of_birth":  "2005-10-07",
    "employment_type":  "SALARIED",
    "gender":  "MALE",
    "state_of_residence":  "West Bengal",
    "occupation":  "Software Engineer",
    "financial_pain_points":  "investments do not yield good returns"
},
        "behavioral_summary": "Standard risk profile.",
        "central_candidates": [],
        "state_candidates": [],
        "final_schemes": []
    }
    result = await matchmaker_agent.ainvoke(state)
    print("FINAL SCHEMES COUNT:", len(result.get("final_schemes", [])))
    print("FINAL SCHEMES:", result.get("final_schemes"))

asyncio.run(run())
