"""Diagnostic: show raw text from first few pages of the bank statement PDF."""
import io
import sys

PDF_PATH = r"C:\Users\ankus\Downloads\62251XXXX_DownloadStatement_1790804605.pdf"
PASSWORD = "SUNA1509"

import pikepdf
import pdfplumber

# Decrypt
buf = io.BytesIO()
with pikepdf.open(PDF_PATH, password=PASSWORD) as pdf:
    pdf.save(buf)
buf.seek(0)

with pdfplumber.open(buf) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")
    # Show raw text of pages 1–4
    for i in range(min(4, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text() or ""
        print(f"{'='*60}")
        print(f"PAGE {i+1} raw text ({len(text)} chars):")
        print(text[:3000])
        print()
