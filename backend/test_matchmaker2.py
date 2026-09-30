import asyncio
import json
from app.agents.matchmaker.graph import matchmaker_agent
from langchain_core.messages import HumanMessage
from app.agents.matchmaker.prompts import RERANK_PROMPT, FORMATTER_PROMPT

async def run():
    state = {
        "user_profile": {
            "name": "Test User",
            "date_of_birth": "2005-10-07",
            "gender": "MALE",
            "state_of_residence": "West Bengal",
            "employment_type": "SALARIED",
            "occupation": "Software Engineer",
            "financial_pain_points": "investments do not yield good returns"
        },
        "behavioral_summary": "Standard risk profile.",
        "central_candidates": [],
        "state_candidates": [],
        "final_schemes": []
    }
    
    # Just run the nodes directly
    from app.agents.matchmaker.graph import central_retrieval_node, state_retrieval_node, consensus_node
    
    c_res = await central_retrieval_node(state)
    s_res = await state_retrieval_node(state)
    
    print("CENTRAL:", len(c_res["central_candidates"]))
    print("STATE:", len(s_res["state_candidates"]))
    
    state.update(c_res)
    state.update(s_res)
    
    con_res = await consensus_node(state)
    print("FINAL:", len(con_res["final_schemes"]))

asyncio.run(run())
