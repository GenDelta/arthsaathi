"""Seed the predatory_clauses LanceDB table with representative patterns.

This script embeds predefined predatory loan clause patterns and inserts them
into the LanceDB table. It uses the currently configured embedding model.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from app.core.config import get_settings
from app.core.llm import get_embeddings
from app.core.logging import configure_logging
from app.db.init_lancedb import init_lancedb

configure_logging()
logger = logging.getLogger(__name__)

CLAUSES = [
    # HIDDEN_FEE
    {
        "clause_text": "A processing fee of 5% plus a technology usage fee of 3% will be deducted from the disbursed amount.",
        "clause_category": "HIDDEN_FEE",
        "severity_weight": 0.7,
        "explanation_template": "The lender is charging hidden processing and technology fees upfront. This reduces the actual money you receive.",
    },
    {
        "clause_text": "The borrower agrees to pay a monthly maintenance fee of Rs. 500 which is subject to change without notice.",
        "clause_category": "HIDDEN_FEE",
        "severity_weight": 0.8,
        "explanation_template": "There are recurring maintenance fees that the lender can increase without telling you.",
    },
    {
        "clause_text": "An express disbursement charge of 10% is applicable for loans approved within 24 hours.",
        "clause_category": "HIDDEN_FEE",
        "severity_weight": 0.9,
        "explanation_template": "You are being charged an exorbitant 10% fee just to get your loan quickly.",
    },
    
    # EXCESSIVE_INTEREST
    {
        "clause_text": "Interest shall accrue at the rate of 1.5% per day on the outstanding principal balance.",
        "clause_category": "EXCESSIVE_INTEREST",
        "severity_weight": 1.0,
        "explanation_template": "The interest rate is extremely high (1.5% PER DAY), which translates to an illegal annual rate.",
    },
    {
        "clause_text": "The annualized percentage rate (APR) for this loan is 85%, compounded weekly.",
        "clause_category": "EXCESSIVE_INTEREST",
        "severity_weight": 1.0,
        "explanation_template": "The interest rate is 85% per year and compounds weekly, which is predatory and far above legal limits.",
    },
    {
        "clause_text": "In addition to the base interest of 36% p.a., a variable risk premium up to 20% may be applied.",
        "clause_category": "EXCESSIVE_INTEREST",
        "severity_weight": 0.9,
        "explanation_template": "The base interest is already very high, and the lender claims the right to add up to 20% more arbitrarily.",
    },
    
    # COERCIVE_RECOVERY
    {
        "clause_text": "The borrower grants the lender full permission to contact all persons in their mobile contact list in case of delayed payment.",
        "clause_category": "COERCIVE_RECOVERY",
        "severity_weight": 1.0,
        "explanation_template": "The lender is demanding access to your phone contacts to harass your friends and family if you miss a payment. This is illegal.",
    },
    {
        "clause_text": "Lender reserves the right to publish the borrower's photo and details on social media as a defaulter.",
        "clause_category": "COERCIVE_RECOVERY",
        "severity_weight": 1.0,
        "explanation_template": "The lender threatens to publicly shame you on social media, which is a prohibited harassment tactic.",
    },
    {
        "clause_text": "Collection agents may visit the borrower's workplace or residence at any time between 6 AM and 11 PM.",
        "clause_category": "COERCIVE_RECOVERY",
        "severity_weight": 0.9,
        "explanation_template": "The lender is claiming the right to send recovery agents to your home or work at unreasonable hours.",
    },
    
    # UNDISCLOSED_PENALTY
    {
        "clause_text": "A late payment penalty of 10% of the principal will be applied for each day the EMI is delayed.",
        "clause_category": "UNDISCLOSED_PENALTY",
        "severity_weight": 1.0,
        "explanation_template": "You will be charged a massive penalty (10% of the entire loan) for every single day you are late.",
    },
    {
        "clause_text": "Any default will result in immediate acceleration of the loan and a flat default charge of Rs. 10,000.",
        "clause_category": "UNDISCLOSED_PENALTY",
        "severity_weight": 0.8,
        "explanation_template": "Missing a payment triggers an immediate demand for the full loan amount plus a heavy Rs. 10,000 penalty.",
    },
    
    # AMBIGUOUS_TERM
    {
        "clause_text": "The lender may alter the terms, interest rate, and repayment schedule at their sole discretion at any time.",
        "clause_category": "AMBIGUOUS_TERM",
        "severity_weight": 0.9,
        "explanation_template": "The lender is giving themselves the power to change your loan terms (like the interest rate) whenever they want.",
    },
    {
        "clause_text": "Additional charges may apply depending on market conditions and administrative costs.",
        "clause_category": "AMBIGUOUS_TERM",
        "severity_weight": 0.7,
        "explanation_template": "The contract mentions 'additional charges' without defining exactly what they are or how much they will cost.",
    },
    
    # ILLEGAL_COLLATERAL_SEIZURE
    {
        "clause_text": "In the event of default, the lender is authorized to seize the borrower's two-wheeler without prior legal notice.",
        "clause_category": "ILLEGAL_COLLATERAL_SEIZURE",
        "severity_weight": 1.0,
        "explanation_template": "The lender is threatening to seize your vehicle without following proper legal procedures or giving notice.",
    },
    {
        "clause_text": "The borrower pledges their smartphone as digital collateral; the lender may remotely lock the device upon missing a payment.",
        "clause_category": "ILLEGAL_COLLATERAL_SEIZURE",
        "severity_weight": 0.9,
        "explanation_template": "The lender plans to remotely lock your phone if you miss a payment, which is an illegal form of digital coercion.",
    }
]

async def seed_clauses() -> None:
    """Embed and insert clauses into LanceDB."""
    settings = get_settings()
    
    # Ensure LanceDB is initialized
    init_lancedb()
    
    import lancedb
    db = lancedb.connect(settings.lancedb_path)
    table = db.open_table("predatory_clauses")
    
    logger.info("Initializing embedding model: %s", settings.embedding_model_name)
    embeddings = get_embeddings()
    
    logger.info("Embedding %d clauses...", len(CLAUSES))
    
    records: list[dict[str, Any]] = []
    
    # Extract texts for bulk embedding if supported, but to be safe we'll do it in batches
    texts = [clause["clause_text"] for clause in CLAUSES]
    try:
        vectors = await embeddings.aembed_documents(texts)
    except Exception as exc:
        logger.warning("aembed_documents failed (%s), falling back to synchronous...", exc)
        vectors = embeddings.embed_documents(texts)
        
    for i, clause in enumerate(CLAUSES):
        records.append({
            "id": str(uuid.uuid4()),
            "vector": vectors[i],
            "clause_text": clause["clause_text"],
            "clause_category": clause["clause_category"],
            "severity_weight": float(clause["severity_weight"]),
            "explanation_template": clause["explanation_template"],
        })
        
    logger.info("Inserting records into LanceDB...")
    table.add(records)
    logger.info("Successfully seeded %d clauses into LanceDB.", len(records))

if __name__ == "__main__":
    asyncio.run(seed_clauses())
