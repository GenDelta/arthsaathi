"""Benchmark script for Scam Scanner and Matchmaker performance."""

import asyncio
import time
import uuid

from app.agents.scam.graph import scam_graph
from app.agents.matchmaker.graph import matchmaker_graph
from app.core.timing import logger as timing_logger

async def run_benchmark():
    timing_logger.setLevel("INFO")
    print("Running performance benchmark for Task 3...")
    
    # 1. Warm-up
    print("Warming up models...")
    from app.core.llm import get_embeddings
    get_embeddings()
    
    # 2. Benchmark Matchmaker
    print("Benchmarking Matchmaker...")
    state_mm = {
        "profile": {
            "state_of_residence": "Maharashtra",
            "employment_type": "GIG_WORKER",
            "average_income": 15000,
            "gender": "Female",
            "date_of_birth": "1990-01-01"
        },
        "candidates": [],
        "matches": []
    }
    
    t0 = time.perf_counter()
    await matchmaker_graph.ainvoke(state_mm)
    t1 = time.perf_counter()
    print(f"Matchmaker execution time: {(t1 - t0) * 1000:.1f}ms")
    
    # 3. Benchmark Scam Scanner
    print("Benchmarking Scam Scanner...")
    state_scam = {
        "document_id": str(uuid.uuid4()),
        "raw_text": "Please pay processing fee of Rs 5000 for loan approval.",
        "verified_text": None,
        "matched_clauses": [],
        "risk_score": None,
        "risk_summary": None,
        "lender_name": None,
        "language": "en"
    }
    
    t0 = time.perf_counter()
    await scam_graph.ainvoke(state_scam)
    t1 = time.perf_counter()
    print(f"Scam Scanner execution time: {(t1 - t0) * 1000:.1f}ms")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
