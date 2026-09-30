import os
from bankstatementparser.hybrid import smart_ingest

os.environ["BSP_HYBRID_MODEL"] = "openai/gpt-oss:20b-cloud"
os.environ["OPENAI_API_BASE"] = "https://ollama.com/v1"
os.environ["OPENAI_API_KEY"] = "502b6fb89ff84b50b7551ac3b4fb7af8.y3tUGK7DuTncmryLRB3_aqi8"

pdf_path = r"C:\Users\ankus\Downloads\account_statement_20260930_045451.pdf"
print(f"Parsing: {pdf_path}")

try:
    result = smart_ingest(pdf_path)
    print("Source method:", result.source_method)
    
    transactions = result.transactions if hasattr(result, "transactions") else result
    print(f"\nFound {len(transactions)} transactions.")
    
    for i, tx in enumerate(transactions[:5]):
        print(f"--- Transaction {i+1} ---")
        print(tx)
        
except Exception as e:
    print(f"Error parsing: {e}")

