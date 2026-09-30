"""Independent verification of PDF totals across time filters."""
import io
import re
import pikepdf
import pdfplumber
from collections import defaultdict
from datetime import datetime, date

PDF_PATH = r"C:\Users\ankus\Downloads\62251XXXX_DownloadStatement_1790804605.pdf"
PASSWORD = "SUNA1509"

buf = io.BytesIO()
with pikepdf.open(PDF_PATH, password=PASSWORD) as pdf:
    pdf.save(buf)
buf.seek(0)

# Regex for the specific format
row_re = re.compile(
    r"^(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    r"\s+\S+"
    r"\s+(.+?)"
    r"\s+([\d,]+\.\d{2})\((Dr|Cr)\)"
    r"\s+([\d,]+\.\d{2})\((Dr|Cr)\)"
    r"\s*$"
)

def parse_date(d_str):
    d_str = d_str.replace("/", "-")
    parts = d_str.split("-")
    return date(int(parts[2]), int(parts[1]), int(parts[0]))

transactions = []
with pdfplumber.open(buf) as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for line in text.splitlines():
            line = line.strip()
            m = row_re.match(line)
            if m:
                date_str, remarks, amt, amt_type, bal, bal_type = m.groups()
                amt_val = float(amt.replace(",", ""))
                d = parse_date(date_str)
                tx_type = "EXPENSE" if amt_type.upper() == "DR" else "INCOME"
                transactions.append((d, tx_type, amt_val))

# Filter Boundaries
# Using the exact JS dates equivalent:
# Today: 2026-10-01
# This Week: >= 2026-09-24 (7 days ago)
# This Month: >= 2026-10-01 (Start of October) -> WAIT! Let's also check Sept 1st just in case.
# Last 3 Months: >= 2026-07-01
# This Year: >= 2026-01-01

filters = {
    "All Time": lambda d: True,
    "This Year (>=2026-01-01)": lambda d: d >= date(2026, 1, 1),
    "Last 3 Months (>=2026-07-01)": lambda d: d >= date(2026, 7, 1),
    "This Month (>=2026-10-01)": lambda d: d >= date(2026, 10, 1),
    "September (>=2026-09-01)": lambda d: d >= date(2026, 9, 1),
    "This Week (>=2026-09-24)": lambda d: d >= date(2026, 9, 24),
}

print(f"Total Transactions parsed: {len(transactions)}\n")

for label, cond in filters.items():
    inc = sum(amt for d, t, amt in transactions if cond(d) and t == "INCOME")
    exp = sum(amt for d, t, amt in transactions if cond(d) and t == "EXPENSE")
    cnt = sum(1 for d, t, amt in transactions if cond(d))
    print(f"--- {label} ---")
    print(f"Count: {cnt}")
    print(f"Income: ₹{inc:,.0f}")
    print(f"Expense: ₹{exp:,.0f}")
    print(f"Net: ₹{inc - exp:,.0f}\n")

