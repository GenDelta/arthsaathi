import asyncio
from app.agents.matchmaker.graph import central_retrieval_node, state_retrieval_node, consensus_node

async def test():
    profile = {
        "user_id": "7a147525-656c-47c9-b909-51d1e36e94ec",
        "employment_type": "SEASONAL",
        "occupation": "farming",
        "income_frequency": "SEASONAL",
        "average_income": 2000.0,
        "financial_pain_points": "Lack of funds to buy new land for farming",
        "date_of_birth": "2004-08-23",
        "state_of_residence": "Madhya Pradesh",
        "gender": "MALE"
    }
    
    state = {
        "user_profile": profile,
        "behavioral_summary": "Standard.",
        "central_candidates": [],
        "state_candidates": [],
        "final_schemes": []
    }
    
    c = await central_retrieval_node(state)
    s = await state_retrieval_node(state)
    
    print(f"Central candidates: {len(c['central_candidates'])}")
    print(f"State candidates:   {len(s['state_candidates'])}")
    print(f"Total:              {len(c['central_candidates']) + len(s['state_candidates'])}")
    
    if s["state_candidates"]:
        print("\nState matches:")
        for sc in s["state_candidates"]:
            print(f"  - {sc['scheme_name']} ({sc['state_name']})")
    
    if c["central_candidates"]:
        print("\nCentral matches:")
        for sc in c["central_candidates"]:
            print(f"  - {sc['scheme_name']}")

    # Now run consensus
    state.update(c)
    state.update(s)
    result = await consensus_node(state)
    print(f"\nFinal schemes after LLM: {len(result['final_schemes'])}")
    for s in result["final_schemes"]:
        print(f"  [{s.get('confidence_score', '?')}%] {s.get('title')}")

asyncio.run(test())
