"""LangGraph for the Extraction & Scam Agent (Phase 3)."""

import json
import logging
import re
from typing import Any, TypedDict
from app.core.timing import timed
import hashlib
from functools import lru_cache

import lancedb
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.scam.prompts import SCAM_SYSTEM_PROMPT
from app.core.config import get_settings
from app.core.llm import get_embeddings, get_llm

logger = logging.getLogger(__name__)


class ScamScanState(TypedDict):
    document_id: str
    raw_text: str                        # from Tesseract, pre-HITL
    verified_text: str | None            # post-HITL, None until user approves
    matched_clauses: list[dict[str, Any]]
    risk_score: float | None
    risk_summary: str | None
    lender_name: str | None
    language: str | None                 # user language preference (e.g. "hi", "mr", "en")



_LANCEDB_CONN = None
def _get_lancedb_table():
    global _LANCEDB_CONN
    if _LANCEDB_CONN is None:
        _LANCEDB_CONN = lancedb.connect(get_settings().lancedb_path)
    return _LANCEDB_CONN.open_table("predatory_clauses")

def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    """Simple word-based chunker."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        if current_length + len(word) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks if chunks else [""]


async def clause_match_node(state: ScamScanState) -> ScamScanState:
    """Embed chunks of the verified text and match against LanceDB predatory_clauses."""
    with timed("scam_clause_match"):
        text = state.get("verified_text") or state.get("raw_text", "")
        if not text.strip():
            return {**state, "matched_clauses": []}
            
        chunks = chunk_text(text)
        embeddings = get_embeddings()
        
        try:
            vectors = await embeddings.aembed_documents(chunks)
        except Exception as exc:
            vectors = embeddings.embed_documents(chunks)
            
        try:
            table = _get_lancedb_table()
        except Exception:
            return {**state, "matched_clauses": []}
            
        all_matches = []
        seen_ids = set()
        
        for vector in vectors:
            results = table.search(vector).limit(3).to_list()
            for r in results:
                if r["id"] not in seen_ids and r.get("_distance", 1.0) < 0.9:
                    seen_ids.add(r["id"])
                    all_matches.append({
                        "id": r["id"],
                        "clause_text": r["clause_text"],
                        "clause_category": r["clause_category"],
                        "severity_weight": r["severity_weight"],
                        "explanation_template": r["explanation_template"],
                        "_distance": r.get("_distance")
                    })
                    
        all_matches.sort(key=lambda x: x.get("_distance", float('inf')))
        return {**state, "matched_clauses": all_matches[:5]}


async def summarize_node(state: ScamScanState) -> ScamScanState:
    """Generate risk summary and score using LLM."""
    with timed("scam_summarize"):
        llm = get_llm(temperature=0.0)
        
        language = state.get("language") or "en"
        text = state.get("verified_text") or state.get("raw_text", "")
        matches = state.get("matched_clauses", [])
        
        # Skip LLM ONLY if there is no text
        if not text.strip():
            return {**state, "risk_summary": "No text found in document.", "risk_score": 0.0}
            
        matches_text = ""
        for idx, m in enumerate(matches, 1):
            matches_text += (
                f"Clause {idx}:\n"
                f"- Pattern: {m['clause_text']}\n"
                f"- Category: {m['clause_category']}\n"
                f"- Severity Weight: {m['severity_weight']}\n"
                f"- Recommended Explanation: {m['explanation_template']}\n\n"
            )
            
        system_msg = SCAM_SYSTEM_PROMPT.format(language=language)
        user_msg_content = f"Document Text:\n{text}\n\nMatched Clauses:\n{matches_text}"
        
        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=user_msg_content)
        ]
        
        response = await llm.ainvoke(messages)
        content = str(response.content)
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return {
                    **state,
                    "risk_summary": data.get("risk_summary", "Summary unavailable."),
                    "risk_score": float(data.get("risk_score", 0.0)),
                    "lender_name": data.get("lender_name")
                }
            except json.JSONDecodeError:
                pass
                
        return {
            **state,
            "risk_summary": content,
            "risk_score": 0.5
        }


def build_scam_graph() -> StateGraph:
    """Build and compile the Scam Scan workflow."""
    workflow = StateGraph(ScamScanState)
    
    workflow.add_node("clause_match_node", clause_match_node)
    workflow.add_node("summarize_node", summarize_node)
    
    workflow.add_edge(START, "clause_match_node")
    workflow.add_edge("clause_match_node", "summarize_node")
    workflow.add_edge("summarize_node", END)
    
    return workflow.compile()

scam_graph = build_scam_graph()
