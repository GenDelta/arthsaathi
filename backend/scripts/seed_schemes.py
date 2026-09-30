import asyncio
import re
import pandas as pd
import aiosqlite
import lancedb
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings

DB_PATH = Path(__file__).parent.parent / "arthsaathi.db"
LANCEDB_PATH = Path(__file__).parent.parent / ".lancedb"
CSV_PATH = Path(__file__).parent.parent / "data" / "scheme_Data.csv"

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Puducherry"
]

def extract_state(text: str, level: str) -> str:
    if str(level).strip().lower() == "central":
        return "ALL"
    text_lower = str(text).lower()
    for state in INDIAN_STATES:
        if state.lower() in text_lower:
            return state
    return "UNKNOWN"

def extract_ages(eligibility_text: str):
    text = str(eligibility_text).lower()
    min_age = 0
    max_age = 999
    
    # Try range e.g. 18 to 40, 18-40, 18 and 40
    range_match = re.search(r"(?:between|from)?\s*(\d{2})\s*(?:to|and|-)\s*(\d{2})\s*(?:years?)", text)
    if range_match:
        min_age = int(range_match.group(1))
        max_age = int(range_match.group(2))
    else:
        # Try single min age
        min_match = re.search(r"(?:minimum|min|above|at least|>|>=)\s*(?:age)?\s*(\d{2})", text)
        if min_match:
            min_age = int(min_match.group(1))
        
        # Try single max age
        max_match = re.search(r"(?:maximum|max|below|under|<|<=)\s*(?:age)?\s*(\d{2})", text)
        if max_match:
            max_age = int(max_match.group(1))
            
    return min_age, max_age

async def seed_schemes():
    print("Loading CSV...")
    df = pd.read_csv(CSV_PATH)
    
    # Fill NAs
    df = df.astype(str).replace("nan", "")
    
    # We will limit to 500 rows for the hackathon to keep ingestion fast
    # Removed limiter to ingest all rows
    
    print("Extracting features using Regex rules...")
    records = []
    for _, row in df.iterrows():
        min_age, max_age = extract_ages(row["eligibility"])
        # Check title and details for state
        state_name = extract_state(row["scheme_name"] + " " + row["details"], row["level"])
        
        records.append({
            "scheme_name": row["scheme_name"],
            "scheme_type": row["level"],
            "state_name": state_name,
            "min_age": min_age,
            "max_age": max_age,
            "details": row["details"],
            "eligibility": row["eligibility"],
            "benefits": row["benefits"],
            "application_process": row["application"],
            "tags": row["tags"]
        })
        
    print("Setting up SQLite `schemes` table...")
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schemes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_name TEXT NOT NULL,
                scheme_type TEXT,
                state_name TEXT,
                min_age INTEGER,
                max_age INTEGER,
                details TEXT,
                eligibility TEXT,
                benefits TEXT,
                application_process TEXT,
                tags TEXT
            )
        """)
        await conn.execute("DELETE FROM schemes") # Clear existing
        
        for r in records:
            await conn.execute("""
                INSERT INTO schemes (scheme_name, scheme_type, state_name, min_age, max_age, details, eligibility, benefits, application_process, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (r["scheme_name"], r["scheme_type"], r["state_name"], r["min_age"], r["max_age"], r["details"], r["eligibility"], r["benefits"], r["application_process"], r["tags"]))
            
        await conn.commit()
        
        # Fetch back with IDs for LanceDB
        cursor = await conn.execute("SELECT id, details, benefits, eligibility, tags FROM schemes")
        db_rows = await cursor.fetchall()

    print("Embedding and setting up LanceDB `schemes_vectors` table...")
    # Setup embedding model (matches the one used for scam scanner)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    vector_data = []
    for row in db_rows:
        scheme_id, details, benefits, eligibility, tags = row
        text_to_embed = f"{details} {benefits} {eligibility} {tags}"
        # Truncate to reasonable length to avoid token limits
        text_to_embed = text_to_embed[:2000] 
        vector_data.append({
            "scheme_id": scheme_id,
            "text": text_to_embed
        })
        
    # Extract texts for batch embedding
    texts = [v["text"] for v in vector_data]
    print(f"Embedding {len(texts)} scheme documents... (this might take a minute)")
    embeddings_list = embeddings.embed_documents(texts)
    
    for i in range(len(vector_data)):
        vector_data[i]["vector"] = embeddings_list[i]
        
    db = lancedb.connect(str(LANCEDB_PATH))
    if "schemes_vectors" in db.table_names():
        db.drop_table("schemes_vectors")
        
    print("Inserting into LanceDB...")
    db.create_table("schemes_vectors", data=vector_data)
    
    print("Seeding complete! Successfully seeded schemes into SQLite and LanceDB.")

if __name__ == "__main__":
    asyncio.run(seed_schemes())



