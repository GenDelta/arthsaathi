"""Verify starting and ending balances for the statement."""
import io
import re
import pikepdf
import pdfplumber

PDF_PATH = r"C:\Users\ankus\Downloads\62251XXXX_DownloadStatement_1790804605.pdf"
PASSWORD = "SUNA1509"

buf = io.BytesIO()
with pikepdf.open(PDF_PATH, password=PASSWORD) as pdf:
    pdf.save(buf)
buf.seek(0)

# Regex to capture the balance as well
row_re = re.compile(
    r"^(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    r"\s+\S+"
    r"\s+(.+?)"
    r"\s+([\d,]+\.\d{2})\((Dr|Cr)\)"
    r"\s+([\d,]+\.\d{2})\((Dr|Cr)\)"
    r"\s*$"
)

first_bal = None
last_bal = None
first_date = None
last_date = None

with pdfplumber.open(buf) as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for line in text.splitlines():
            line = line.strip()
            m = row_re.match(line)
            if m:
                date_str, remarks, amt, amt_type, bal, bal_type = m.groups()
                
                # record first balance
                if first_bal is None:
                    first_bal = (bal, bal_type)
                    first_date = date_str
                
                # continually update last balance
                last_bal = (bal, bal_type)
                last_date = date_str

print(f"First transaction date: {first_date}, Balance after: {first_bal[0]} ({first_bal[1]})")
print(f"Last transaction date:  {last_date}, Balance after: {last_bal[0]} ({last_bal[1]})")
