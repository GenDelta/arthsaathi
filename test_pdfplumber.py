import pdfplumber
import sys

pdf_path = r"C:\Users\ankus\Downloads\account_statement_20260930_045451.pdf"
print(f"Extracting tables from {pdf_path}...\n")

try:
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                print(f"--- Page {i+1} ---")
                for table_idx, table in enumerate(tables):
                    print(f"Table {table_idx+1}:")
                    for row in table[:8]: # Print first 8 rows
                        print([str(cell).strip().replace("\n", " ") if cell else "" for cell in row])
                    if len(table) > 8:
                        print(f"... and {len(table)-8} more rows.")
                    print("-" * 40)
            else:
                print(f"--- Page {i+1} ---")
                print("No tables detected mathematically. (Could be a scanned image or borderless table).")
except Exception as e:
    print(f"Error: {e}")

