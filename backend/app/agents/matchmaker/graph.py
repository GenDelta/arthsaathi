import json
import logging
from typing import List, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
import lancedb
import aiosqlite

from app.core.config import get_settings
from app.core.llm import get_llm
from app.agents.matchmaker.state import MatchmakerState
from app.agents.matchmaker.prompts import RERANK_PROMPT, FORMATTER_PROMPT

logger = logging.getLogger(__name__)

def _get_lancedb_table():
    db = lancedb.connect(str(get_settings().lancedb_path))
    return db.open_table("schemes_vectors")

def _get_user_embedding(profile: dict, focus: str = "general") -> list:
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    gender = profile.get("gender", "").lower()
    state = profile.get("state_of_residence", "")
    emp_type = profile.get("employment_type", "").replace("_", " ").lower()
    occupation = profile.get("occupation", "")
    pain_points = profile.get("financial_pain_points", "")
    dob = profile.get("date_of_birth", "")
    
    age_str = ""
    if dob:
        try:
            from datetime import date
            birth_year = int(str(dob)[:4])
            age = date.today().year - birth_year
            if age < 25:
                age_str = "youth young"
            elif age > 55:
                age_str = "senior elderly"
        except:
            pass
    
    if focus == "central":
        # Emphasise occupation and national schemes, drop state name
        query = (
            f"central government national scheme benefit welfare assistance {gender} {age_str} "
            f"{emp_type} worker {occupation} India income support subsidy {pain_points}"
        ).strip()
    else:
        # Emphasise state and local context
        query = (
            f"government scheme benefit welfare assistance {gender} {age_str} "
            f"{emp_type} worker {occupation} {state} "
            f"income support subsidy {pain_points}"
        ).strip()
    
    return embeddings.embed_query(query)

async def central_retrieval_node(state: MatchmakerState):
    profile = state.get("user_profile", {})
    try:
        table = _get_lancedb_table()
        query_vec = _get_user_embedding(profile, focus="central")
        results = table.search(query_vec).limit(50).to_list()
        
        db_path = get_settings().database_path
        candidate_ids = [r["scheme_id"] for r in results]
        candidates = []
        if candidate_ids:
            placeholders = ",".join("?" * len(candidate_ids))
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    f"SELECT * FROM schemes WHERE id IN ({placeholders}) AND scheme_type = 'Central'", 
                    candidate_ids
                )
                rows = await cursor.fetchall()
                for r in rows:
                    candidates.append(dict(r))
                    
        return {"central_candidates": candidates}
    except Exception as e:
        logger.error(f"Central retrieval error: {e}")
        return {"central_candidates": []}

async def state_retrieval_node(state: MatchmakerState):
    profile = state.get("user_profile", {})
    state_name = profile.get("state_of_residence", "")
    
    try:
        table = _get_lancedb_table()
        query_vec = _get_user_embedding(profile, focus="state")
        results = table.search(query_vec).limit(60).to_list()
        
        db_path = get_settings().database_path
        candidate_ids = [r["scheme_id"] for r in results]
        candidates = []
        if candidate_ids:
            placeholders = ",".join("?" * len(candidate_ids))
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    f"SELECT * FROM schemes WHERE id IN ({placeholders}) AND scheme_type = 'State'", 
                    candidate_ids
                )
                rows = await cursor.fetchall()
                for r in rows:
                    db_state = str(r["state_name"]).lower().strip()
                    user_state = state_name.lower().strip()
                    if user_state and (user_state in db_state or db_state in user_state or db_state in ("all", "nan", "", "all india", "pan india")):
                        candidates.append(dict(r))
                        
        return {"state_candidates": candidates}
    except Exception as e:
        logger.error(f"State retrieval error: {e}")
        return {"state_candidates": []}

async def consensus_node(state: MatchmakerState):
    central = state.get("central_candidates", [])
    local = state.get("state_candidates", [])
    all_candidates = central + local
    
    if not all_candidates:
        return {"final_schemes": []}
    
    # Build candidates text — show ALL candidates, not just first 15
    candidates_text = ""
    for c in all_candidates:
        candidates_text += f"ID: {c['id']} | Name: {c['scheme_name']} | Benefits: {c['benefits']}\n"
        
    prompt = RERANK_PROMPT.format(
        profile=json.dumps(state.get("user_profile", {})),
        behavioral_summary=state.get("behavioral_summary", "None"),
        candidates=candidates_text
    )
    
    llm = get_llm(temperature=0.0)
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    
    try:
        content = res.content
        start = content.find("[")
        end = content.rfind("]") + 1
        top_ids = json.loads(content[start:end])
        if not top_ids:
            top_ids = [c["id"] for c in all_candidates[:5]]
    except:
        top_ids = [c["id"] for c in all_candidates[:5]]
    
    logger.info(f"Consensus selected IDs: {top_ids}")
        
    final_schemes = []
    for c in all_candidates:
        if c["id"] in top_ids:
            format_prompt = FORMATTER_PROMPT.format(scheme_details=json.dumps(c))
            format_res = await llm.ainvoke([HumanMessage(content=format_prompt)])
            try:
                f_content = format_res.content
                s = f_content.find("{")
                e = f_content.rfind("}") + 1
                formatted = json.loads(f_content[s:e])
                formatted["id"] = c["id"]
                final_schemes.append(formatted)
            except Exception as ex:
                # Formatter failed — build a safe fallback card from raw data
                logger.warning(f"Formatter failed for scheme {c['id']}: {ex}. Using fallback.")
                final_schemes.append({
                    "id": c["id"],
                    "title": c.get("scheme_name", "Unknown Scheme"),
                    "ministry": c.get("scheme_type", "Government"),
                    "benefit_summary": c.get("benefits", "")[:300],
                    "application_steps": c.get("application_process", "Visit your nearest CSC or government office.")[:300],
                    "eligibility": c.get("eligibility_criteria", "")[:200],
                    "confidence_score": 75,
                })
                
    # Sort by confidence descending
    final_schemes.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
    
    # Adaptive display: if 5+ schemes cleared 70%, show only top 3 (high quality set)
    # Otherwise show all 5 (broader net for sparse profiles)
    high_confidence = [s for s in final_schemes if s.get("confidence_score", 0) > 70]
    if len(high_confidence) >= 5:
        final_schemes = final_schemes[:3]
    else:
        final_schemes = final_schemes[:5]
    
    logger.info(f"Returning {len(final_schemes)} schemes (high_confidence count: {len(high_confidence)})")
    return {"final_schemes": final_schemes}

def build_matchmaker_graph():
    workflow = StateGraph(MatchmakerState)
    
    workflow.add_node("central_retrieval", central_retrieval_node)
    workflow.add_node("state_retrieval", state_retrieval_node)
    workflow.add_node("consensus", consensus_node)
    
    workflow.add_edge(START, "central_retrieval")
    workflow.add_edge("central_retrieval", "state_retrieval")
    
    
    workflow.add_edge("state_retrieval", "consensus")
    
    workflow.add_edge("consensus", END)
    
    return workflow.compile()

matchmaker_agent = build_matchmaker_graph()



