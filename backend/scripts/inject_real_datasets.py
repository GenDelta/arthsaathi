"""Script to ingest real-world scam/spam datasets into the LanceDB vector database."""

import asyncio
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

async def process_datasets(limit_per_dataset: int | None = None) -> None:
    # Ensure dependencies are available
    try:
        import pandas as pd
        from datasets import load_dataset
    except ImportError:
        logger.error("Please ensure 'pandas' and 'datasets' are installed.")
        return

    scam_records = []

    # 1. Hugging Face Dataset: mshenoda/spam-messages
    try:
        logger.info("Loading Hugging Face dataset: mshenoda/spam-messages")
        ds = load_dataset("mshenoda/spam-messages", split="train")
        df_hf = ds.to_pandas()
        spam_hf = df_hf[df_hf['label'] == 'spam']['text'].dropna().unique().tolist()
        
        target_hf = spam_hf[:limit_per_dataset] if limit_per_dataset else spam_hf
        for text in target_hf:
            scam_records.append({"text": text, "category": "SMS_SPAM"})
        logger.info(f"Added {len(target_hf)} scam messages from HF.")
    except Exception as e:
        logger.error(f"Failed to load HF dataset: {e}")

    # 2. Local Dataset: spam.csv
    spam_csv_path = Path("data/spam.csv")
    if spam_csv_path.exists():
        try:
            logger.info("Loading local dataset: spam.csv")
            df_csv = pd.read_csv(spam_csv_path, encoding='latin1') 
            if 'v1' in df_csv.columns and 'v2' in df_csv.columns:
                spam_csv = df_csv[df_csv['v1'] == 'spam']['v2'].dropna().unique().tolist()
                
                target_csv = spam_csv[:limit_per_dataset] if limit_per_dataset else spam_csv
                for text in target_csv:
                    scam_records.append({"text": text, "category": "SMS_SPAM"})
                logger.info(f"Added {len(target_csv)} scam messages from spam.csv.")
        except Exception as e:
            logger.error(f"Failed to load spam.csv: {e}")

    # 3. Local Dataset: phishing_dataset_with_category.csv
    phishing_csv_path = Path("data/phishing_dataset_with_category.csv")
    if phishing_csv_path.exists():
        try:
            logger.info("Loading local dataset: phishing_dataset_with_category.csv")
            df_phish = pd.read_csv(phishing_csv_path)
            if 'label' in df_phish.columns and 'text' in df_phish.columns:
                phish_data = df_phish[df_phish['label'].astype(str).str.contains('phishing', case=False, na=False)]
                count = 0
                for _, row in phish_data.iterrows():
                    if limit_per_dataset and count >= limit_per_dataset:
                        break
                    cat = row['category'] if 'category' in row and pd.notna(row['category']) else "PHISHING"
                    scam_records.append({"text": str(row['text']), "category": str(cat).upper()})
                    count += 1
                logger.info(f"Added {count} scam messages from phishing_dataset_with_category.csv.")
        except Exception as e:
            logger.error(f"Failed to load phishing_dataset: {e}")

    # 4. Local Dataset: Phishing_Email.csv
    phish_email_path = Path("data/Phishing_Email.csv")
    if phish_email_path.exists():
        try:
            logger.info("Loading local dataset: Phishing_Email.csv")
            df_email = pd.read_csv(phish_email_path)
            if 'Email Type' in df_email.columns and 'Email Text' in df_email.columns:
                phish_emails = df_email[df_email['Email Type'] == 'Phishing Email']['Email Text'].dropna().unique().tolist()
                
                target_email = phish_emails[:limit_per_dataset] if limit_per_dataset else phish_emails
                for text in target_email:
                    trunc_text = str(text)[:1000] # Truncate to save tokens/memory
                    scam_records.append({"text": trunc_text, "category": "EMAIL_PHISHING"})
                logger.info(f"Added {len(target_email)} scam emails from Phishing_Email.csv.")
        except Exception as e:
            logger.error(f"Failed to load Phishing_Email.csv: {e}")

    logger.info(f"Total scam records to embed: {len(scam_records)}")
    if not scam_records:
        logger.warning("No scam records found. Exiting.")
        return

    # Ingestion into LanceDB
    settings = get_settings()
    
    import lancedb
    db = lancedb.connect(settings.lancedb_path)
    
    # Drop existing table because it was likely created with 1536 dim (OpenAI) 
    # instead of 384 dim (all-MiniLM-L6-v2), which causes an arrow Cast error.
    logger.info("Dropping existing predatory_clauses table to reset vector dimensions...")
    try:
        db.drop_table("predatory_clauses")
    except Exception:
        pass
        
    init_lancedb()
    table = db.open_table("predatory_clauses")
    
    logger.info("Initializing embedding model...")
    embeddings = get_embeddings()
    
    batch_size = 100
    db_records = []
    
    for i in range(0, len(scam_records), batch_size):
        batch = scam_records[i:i + batch_size]
        batch_texts = [r["text"] for r in batch]
        logger.info(f"Embedding batch {i // batch_size + 1} of {(len(scam_records) - 1) // batch_size + 1}...")
        
        try:
            vectors = await embeddings.aembed_documents(batch_texts)
        except Exception:
            vectors = embeddings.embed_documents(batch_texts)
            
        for record, vector in zip(batch, vectors):
            db_records.append({
                "id": str(uuid.uuid4()),
                "vector": vector,
                "clause_text": record["text"],
                "clause_category": record["category"],
                "severity_weight": 1.0,
                "explanation_template": "This message matches real-world verified scam/phishing patterns.",
            })
            
    logger.info("Inserting records into LanceDB...")
    table.add(db_records)
    logger.info(f"Successfully injected {len(db_records)} real-world scam messages into the vector DB!")

if __name__ == "__main__":
    # Remove the limit entirely to process all ~59,000+ records!
    asyncio.run(process_datasets(limit_per_dataset=None))
