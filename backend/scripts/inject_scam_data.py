"""Script to inject an external JSON dataset of scam SMS/emails into LanceDB."""

import argparse
import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

# Add backend directory to path so we can import 'app'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.llm import get_embeddings
from app.core.logging import configure_logging
from app.db.init_lancedb import init_lancedb

configure_logging()
logger = logging.getLogger(__name__)

async def inject_dataset(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        logger.error("Dataset file not found: %s", filepath)
        sys.exit(1)
        
    with open(path, encoding="utf-8") as f:
        try:
            dataset = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON dataset: %s", e)
            sys.exit(1)
            
    if not isinstance(dataset, list):
        logger.error("Dataset must be a JSON array of objects.")
        sys.exit(1)

    settings = get_settings()
    init_lancedb()
    
    import lancedb
    db = lancedb.connect(settings.lancedb_path)
    
    # We inject into predatory_clauses because the LangGraph agent is wired to use it.
    table = db.open_table("predatory_clauses")
    
    logger.info("Initializing embedding model...")
    embeddings = get_embeddings()
    
    texts = [item["text"] for item in dataset]
    logger.info("Embedding %d scam messages...", len(texts))
    
    try:
        vectors = await embeddings.aembed_documents(texts)
    except Exception as exc:
        logger.warning("aembed_documents failed (%s), falling back to synchronous...", exc)
        vectors = embeddings.embed_documents(texts)
        
    records = []
    for i, item in enumerate(dataset):
        records.append({
            "id": str(uuid.uuid4()),
            "vector": vectors[i],
            "clause_text": item["text"],
            "clause_category": item.get("category", "UNKNOWN_SCAM"),
            "severity_weight": float(item.get("severity", 1.0)),
            "explanation_template": item.get("explanation", "Potential fraud detected."),
        })
        
    logger.info("Inserting records into LanceDB...")
    table.add(records)
    logger.info("Successfully injected %d scam messages into the vector DB.", len(records))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject a dataset of scam messages into the vector DB.")
    parser.add_argument("file", help="Path to the JSON dataset file")
    args = parser.parse_args()
    
    asyncio.run(inject_dataset(args.file))
