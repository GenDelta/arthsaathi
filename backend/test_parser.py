"""Test the new precise parser against the actual PDF."""
import sys
sys.path.insert(0, ".")

from app.services.pdf_parser import parse_bank_statement

with open(r"C:\Users\ankus\Downloads\62251XXXX_DownloadStatement_1790804605.pdf", "rb") as f:
    data = f.read()

txs = parse_bank_statement(data, password="SUNA1509")
print(f"\nTotal transactions: {len(txs)}")
print("\nFirst 10:")
for t in txs[:10]:
    print(f"  {t['date']} | {t['type']:7} | {t['category']:20} | {t['amount']:>10.2f} | {t['description'][:60]}")

income = sum(t['amount'] for t in txs if t['type'] == 'INCOME')
expense = sum(t['amount'] for t in txs if t['type'] == 'EXPENSE')
print(f"\nTotal INCOME:  ₹{income:,.2f}")
print(f"Total EXPENSE: ₹{expense:,.2f}")
print(f"Net savings:   ₹{income - expense:,.2f}")
