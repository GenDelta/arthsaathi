import asyncio
from app.agents.matchmaker.graph import central_retrieval_node, state_retrieval_node

async def test():
    state = {
        "user_profile": {
            "name": "Vedant Chavle",
            "date_of_birth": "2005-10-07",
            "gender": "MALE",
            "state_of_residence": "West Bengal",
            "employment_type": "SALARIED",
            "occupation": "Software Engineer",
            "financial_pain_points": "investments do not yield good returns"
        },
        "behavioral_summary": "Standard.",
        "central_candidates": [],
        "state_candidates": [],
        "final_schemes": []
    }
    
    c = await central_retrieval_node(state)
    s = await state_retrieval_node(state)
    
    total = len(c["central_candidates"]) + len(s["state_candidates"])
    print(f"Central candidates: {len(c['central_candidates'])}")
    print(f"State candidates:   {len(s['state_candidates'])}")
    print(f"Total without filter: {total}")
    if s["state_candidates"]:
        print("State matches:")
        for sc in s["state_candidates"]:
            print(f"  - {sc['scheme_name']} ({sc['state_name']})")

asyncio.run(test())
