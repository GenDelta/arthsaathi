"""Deterministic bank-statement PDF parser for ArthSaathi.

Extracts tabular transaction data from PDF bank statements using pdfplumber.
Encrypted PDFs are decrypted in-memory with pikepdf before parsing.

Dependencies (must be present in pyproject.toml):
    pdfplumber>=0.11.0
    pikepdf>=9.0.0
"""

from __future__ import annotations

import io
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ─── Category keyword maps ────────────────────────────────────────────────────

_INCOME_KEYWORDS: dict[str, str] = {
    # GIG_WAGE — platform delivery income
    "gig":        "GIG_WAGE",
    "delivery":   "GIG_WAGE",
    "zomato":     "GIG_WAGE",
    "swiggy":     "GIG_WAGE",
    "rapido":     "GIG_WAGE",
    "dunzo":      "GIG_WAGE",
    "blinkit":    "GIG_WAGE",
    # AGRICULTURAL_SALE — farm/crop income
    "crop":       "AGRICULTURAL_SALE",
    "harvest":    "AGRICULTURAL_SALE",
    "kisan":      "AGRICULTURAL_SALE",
    "agriculture":"AGRICULTURAL_SALE",
    "mandi":      "AGRICULTURAL_SALE",
    "farm":       "AGRICULTURAL_SALE",
    # OTHER_INCOME — salary, transfers, refunds, interest
    "salary":     "OTHER_INCOME",
    "sal ":       "OTHER_INCOME",
    "stipend":    "OTHER_INCOME",
    "wages":      "OTHER_INCOME",
    "upi received":"OTHER_INCOME",
    "upi credit": "OTHER_INCOME",
    "neft credit":"OTHER_INCOME",
    "rtgs credit":"OTHER_INCOME",
    "imps credit":"OTHER_INCOME",
    "credit":     "OTHER_INCOME",
    "refund":     "OTHER_INCOME",
    "cashback":   "OTHER_INCOME",
    "interest":   "OTHER_INCOME",
    "dividend":   "OTHER_INCOME",
}

_EXPENSE_KEYWORDS: dict[str, str] = {
    # FOOD
    "zomato":     "FOOD",
    "swiggy":     "FOOD",
    "food":       "FOOD",
    "restaurant": "FOOD",
    "cafe":       "FOOD",
    "grocery":    "FOOD",
    "bigbasket":  "FOOD",
    "blinkit":    "FOOD",
    "zepto":      "FOOD",
    # TRANSPORT
    "metro":      "TRANSPORT",
    "uber":       "TRANSPORT",
    "ola":        "TRANSPORT",
    "rapido":     "TRANSPORT",
    "irctc":      "TRANSPORT",
    "railway":    "TRANSPORT",
    "bus":        "TRANSPORT",
    "fuel":       "TRANSPORT",
    "petrol":     "TRANSPORT",
    # UTILITIES
    "electricity":"UTILITIES",
    "electric":   "UTILITIES",
    "water bill": "UTILITIES",
    "gas bill":   "UTILITIES",
    "mobile recharge":"UTILITIES",
    "recharge":   "UTILITIES",
    "broadband":  "UTILITIES",
    "internet":   "UTILITIES",
    "jio":        "UTILITIES",
    "airtel":     "UTILITIES",
    "bsnl":       "UTILITIES",
    "vodafone":   "UTILITIES",
    "vi ":        "UTILITIES",
    # DEBT_REPAYMENT
    "emi":        "DEBT_REPAYMENT",
    "loan":       "DEBT_REPAYMENT",
    "rent":       "DEBT_REPAYMENT",
    "housing":    "DEBT_REPAYMENT",
    # HEALTHCARE
    "hospital":   "HEALTHCARE",
    "pharmacy":   "HEALTHCARE",
    "medical":    "HEALTHCARE",
    "doctor":     "HEALTHCARE",
    "clinic":     "HEALTHCARE",
    "apollo":     "HEALTHCARE",
    "netmeds":    "HEALTHCARE",
    "1mg":        "HEALTHCARE",
    # DISCRETIONARY (shopping, entertainment)
    "amazon":     "DISCRETIONARY",
    "flipkart":   "DISCRETIONARY",
    "myntra":     "DISCRETIONARY",
    "netflix":    "DISCRETIONARY",
    "hotstar":    "DISCRETIONARY",
    "spotify":    "DISCRETIONARY",
}

# ─── Column detection ─────────────────────────────────────────────────────────

_DATE_HEADERS = {"date", "txn date", "transaction date", "value date", "posting date"}
_DESC_HEADERS = {
    "narration", "description", "particulars", "details", "remarks",
    "transaction details", "narration/chq./ref. no.", "ref no./cheque no.",
}
_DEBIT_HEADERS = {"debit", "withdrawal", "dr", "debit amount", "withdrawal amount"}
_CREDIT_HEADERS = {"credit", "deposit", "cr", "credit amount", "deposit amount"}
_AMOUNT_HEADERS = {"amount", "amount()", "amount( )", "txn amount", "transaction amount", "amount(inr)", "amount (inr)", "amount(rs)"}
_BALANCE_HEADERS = {"balance", "closing balance", "available balance", "running balance", "balance( )", "balance()"}


def _normalise_header(h: str) -> str:
    return re.sub(r"\s+", " ", h or "").strip().lower()


def _find_column_indices(headers: list[str]) -> dict[str, int | None]:
    """Map semantic column roles to their positional indices."""
    indices: dict[str, int | None] = {
        "date": None, "description": None,
        "debit": None, "credit": None, "balance": None, "amount": None,
    }
    for i, raw in enumerate(headers):
        h = _normalise_header(raw)
        if h in _DATE_HEADERS and indices["date"] is None:
            indices["date"] = i
        elif h in _DESC_HEADERS and indices["description"] is None:
            indices["description"] = i
        elif h in _DEBIT_HEADERS and indices["debit"] is None:
            indices["debit"] = i
        elif h in _CREDIT_HEADERS and indices["credit"] is None:
            indices["credit"] = i
        elif h in _AMOUNT_HEADERS and indices["amount"] is None:
            indices["amount"] = i
        elif h in _BALANCE_HEADERS and indices["balance"] is None:
            indices["balance"] = i
    return indices


# ─── Amount parsing ───────────────────────────────────────────────────────────

def _parse_amount(raw: Any) -> float | None:
    """Convert a raw cell value to a float, stripping currency symbols/commas."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text in {"-", "–", "—", "nil", "n/a"}:
        return None
        
    # Strip common prefixes/suffixes completely to avoid leaving stray dots (like from 'Rs.' or 'Dr.')
    text = re.sub(r"(?i)rs\.?|inr|cr\.?|dr\.?", "", text)
    text = re.sub(r"[a-zA-Z\s]+", "", text)
    
    # Super robust: strip everything except digits, decimal point, and minus sign
    text = re.sub(r"[^0-9\.-]", "", text)
    try:
        return float(text)
    except ValueError:
        return None


# ─── Category inference ───────────────────────────────────────────────────────

def _infer_category(description: str, tx_type: str) -> str:
    desc_lower = description.lower()
    if tx_type == "INCOME":
        for keyword, category in _INCOME_KEYWORDS.items():
            if keyword in desc_lower:
                return category
        return "OTHER_INCOME"
    else:  # EXPENSE
        for keyword, category in _EXPENSE_KEYWORDS.items():
            if keyword in desc_lower:
                return category
        return "OTHER_EXPENSE"


# ─── Date normalisation ───────────────────────────────────────────────────────

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

def _normalize_date(raw: str) -> str:
    """Convert any common Indian bank date format to ISO YYYY-MM-DD."""
    raw = re.sub(r"\s+", "", raw).strip()
    # DD-MM-YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", raw)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    # DD-MM-YY (2-digit year)
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2})$", raw)
    if m:
        d, mo, y = m.groups()
        year = f"20{y}" if int(y) < 70 else f"19{y}"
        return f"{year}-{mo.zfill(2)}-{d.zfill(2)}"
    # DD-Mon-YYYY (e.g. 03-Sep-2026)
    m = re.match(r"^(\d{1,2})[-/]([A-Za-z]{3})[-/](\d{4})$", raw, re.IGNORECASE)
    if m:
        d, mon, y = m.groups()
        mo = _MONTH_MAP.get(mon.lower())
        if mo:
            return f"{y}-{mo}-{d.zfill(2)}"
    return raw  # already ISO or unrecognised


# ─── Text-layout statement parser ────────────────────────────────────────────
# Handles: DD-MM-YYYY  TXNID  REMARKS  AMOUNT(Dr|Cr)  BALANCE(Dr|Cr)
# Also handles space-separated columns without (Dr)/(Cr) markers.

_ROW_RE = re.compile(
    r"^(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"   # group 1: date
    r"\s+\S+"                                 # transaction ID (skip)
    r"\s+(.+?)"                               # group 2: remarks (non-greedy)
    r"\s+([\d,]+\.\d{2})\((Dr|Cr)\)"        # group 3: amount, group 4: Dr/Cr
    r"\s+[\d,]+\.\d{2}\((?:Dr|Cr)\)"        # balance (skip)
    r"\s*$"
)

# Fallback: lines where amount doesn't have (Dr)/(Cr) but we can infer from position
_ROW_PLAIN_RE = re.compile(
    r"^(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    r"\s+\S+"
    r"\s+(.+?)"
    r"\s+([\d,]+\.\d{2})"
    r"\s+([\d,]+\.\d{2})"
    r"\s*$"
)

def _parse_text_page(text: str) -> list[dict]:
    """Parse a page of raw bank statement text into transactions.

    Supports two formats:
    1. Structured: DATE  TXNID  REMARKS  AMOUNT(Dr|Cr)  BALANCE(Dr|Cr)
    2. Plain:      DATE  TXNID  REMARKS  AMOUNT  BALANCE  (type inferred from keywords)
    """
    results: list[dict] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Format 1: has explicit (Dr)/(Cr) markers — most reliable
        m = _ROW_RE.match(line)
        if m:
            date_str, remarks, amount_str, dr_cr = m.group(1), m.group(2), m.group(3), m.group(4)
            tx_type = "EXPENSE" if dr_cr.upper() == "DR" else "INCOME"
            try:
                amount = round(float(amount_str.replace(",", "")), 2)
            except ValueError:
                continue
            if amount <= 0:
                continue
            description = re.sub(r"\s+", " ", remarks).strip()
            results.append({
                "date": _normalize_date(date_str),
                "description": description[:300],
                "amount": amount,
                "type": tx_type,
                "category": _infer_category(description, tx_type),
            })
            continue

        # Format 2: no Dr/Cr marker — infer type from keywords in remarks
        m2 = _ROW_PLAIN_RE.match(line)
        if m2:
            date_str, remarks, amount_str, _ = m2.group(1), m2.group(2), m2.group(3), m2.group(4)
            try:
                amount = round(float(amount_str.replace(",", "")), 2)
            except ValueError:
                continue
            if amount <= 0:
                continue
            description = re.sub(r"\s+", " ", remarks).strip()
            desc_lower = description.lower()
            if any(k in desc_lower for k in ["cr/", "/cr/", "upiab", "credit", "received", "refund", "salary", "interest", "cashback", "neft cr", "imps cr"]):
                tx_type = "INCOME"
            else:
                tx_type = "EXPENSE"
            results.append({
                "date": _normalize_date(date_str),
                "description": description[:300],
                "amount": amount,
                "type": tx_type,
                "category": _infer_category(description, tx_type),
            })

    return results


def _row_to_transaction(
    row: list[Any],
    col_idx: dict[str, int | None],
) -> dict[str, Any] | None:
    """Convert a raw table row to a transaction dict. Returns None for malformed rows."""
    try:
        def cell(key: str) -> str:
            idx = col_idx.get(key)
            if idx is None or idx >= len(row):
                return ""
            return str(row[idx] or "").strip()

        date = cell("date")
        description = cell("description")
        debit_raw = cell("debit")
        credit_raw = cell("credit")

        amount_raw = cell("amount")

        # Skip rows that look like headers repeated mid-table or are empty
        if not date or not description:
            logger.warning("Row skipped: missing date (%r) or desc (%r)", date, description)
            return None
        if _normalise_header(date) in _DATE_HEADERS:
            return None  # repeated header row

        debit = _parse_amount(debit_raw)
        credit = _parse_amount(credit_raw)
        
        tx_type = None
        amount = 0.0

        if credit and (not debit or credit > 0):
            tx_type = "INCOME"
            amount = credit
        elif debit and debit > 0:
            tx_type = "EXPENSE"
            amount = debit
        elif amount_raw:
            raw_str = amount_raw.strip().lower()
            amt_val = _parse_amount(raw_str)
            if not amt_val:
                logger.warning("Row skipped: amount_raw %r failed parsing", amount_raw)
                return None
            
            if "cr" in raw_str:
                tx_type = "INCOME"
            elif "dr" in raw_str:
                tx_type = "EXPENSE"
            elif raw_str.startswith("-"):
                tx_type = "EXPENSE"
            else:
                desc_lower = description.lower()
                if any(k in desc_lower for k in ["cr/", "/cr/", "upiab", "credit", "received", "refund", "salary", "interest", "cashback", "neft cr", "imps cr"]):
                    tx_type = "INCOME"
                else:
                    tx_type = "EXPENSE"
            amount = abs(amt_val)
        else:
            logger.warning("Row skipped: no debit, credit, or amount. %r %r %r", debit_raw, credit_raw, amount_raw)
            return None  # no usable amount

        category = _infer_category(description, tx_type)
        logger.info("Row SUCCESS: %r %r %r %r", date, description, amount, tx_type)

        return {
            "date": _normalize_date(date),
            "description": description,
            "amount": round(amount, 2),
            "type": tx_type,
            "category": category,
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("Skipping malformed row %r: %s", row, exc)
        return None


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_bank_statement(
    file_bytes: bytes,
    password: str | None = None,
) -> list[dict[str, Any]]:
    """Parse a bank-statement PDF and return a list of transaction dicts.

    Args:
        file_bytes: Raw bytes of the PDF file.
        password: Decryption password. Used only if explicitly provided;
                  no guessing is attempted.

    Returns:
        A list of dicts, each with keys:
            ``date``, ``description``, ``amount`` (float),
            ``type`` ("INCOME"|"EXPENSE"), ``category`` (str).

    Raises:
        ImportError: If pdfplumber or pikepdf are not installed.
        ValueError: If the PDF cannot be opened (e.g. wrong password).
    """
    try:
        import pdfplumber  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "pdfplumber is required for PDF parsing. Add it to pyproject.toml."
        ) from exc

    # Decrypt in-memory if a password is given
    if password is not None:
        try:
            import pikepdf  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "pikepdf is required for encrypted PDF support. Add it to pyproject.toml."
            ) from exc

        try:
            buf = io.BytesIO()
            with pikepdf.open(io.BytesIO(file_bytes), password=password) as pdf:
                pdf.save(buf)
            buf.seek(0)
            pdf_source: bytes | io.BytesIO = buf
        except Exception as exc:
            exc_repr = repr(exc)
            exc_str = str(exc)
            if "PasswordError" in exc_repr or "invalid password" in exc_str.lower():
                raise ValueError("The provided password is incorrect. Please try again.") from exc
            raise ValueError(f"Could not open encrypted PDF: {exc}") from exc
    else:
        pdf_source = io.BytesIO(file_bytes)

    transactions: list[dict[str, Any]] = []

    # Try multiple extraction strategies for borderless Indian bank statement layouts
    _STRATEGIES = [
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
        {"vertical_strategy": "lines", "horizontal_strategy": "text"},
        {"vertical_strategy": "text", "horizontal_strategy": "lines"},
        {"vertical_strategy": "text", "horizontal_strategy": "text"},
    ]

    def _best_tables(page: Any) -> list:
        for strategy in _STRATEGIES:
            try:
                tbls = page.extract_tables(table_settings=strategy)
                if tbls and any(len(t) > 2 for t in tbls if t):
                    return tbls
            except Exception:
                continue
        return []

    try:
        with pdfplumber.open(pdf_source) as pdf:
            logger.info("PDF opened: %d pages", len(pdf.pages))
            
            # Persist header state across all pages and tables.
            # Bank statements often only print the header on the very first page.
            global_col_idx: dict[str, int | None] = {
                "date": None, "description": None,
                "debit": None, "credit": None, "balance": None,
            }
            header_locked = False

            for page_num, page in enumerate(pdf.pages, start=1):
                tables = _best_tables(page)
                if not tables:
                    # Fall back to raw text parsing for text-layout PDFs (no visible table borders)
                    raw_text = page.extract_text() or ""
                    if raw_text.strip():
                        text_txs = _parse_text_page(raw_text)
                        if text_txs:
                            logger.info("Page %d: text fallback extracted %d transactions", page_num, len(text_txs))
                            transactions.extend(text_txs)
                        else:
                            logger.info("Page %d: no tables and text fallback found nothing", page_num)
                    continue

                logger.info("Page %d: %d table(s) found", page_num, len(tables))

                for t_idx, table in enumerate(tables):
                    if not table:
                        continue

                    logger.info("Page %d table %d: %d rows | first row: %s",
                                page_num, t_idx, len(table),
                                [str(c or "")[:20] for c in table[0]])

                    for row_idx, row in enumerate(table):
                        if not row:
                            continue

                        if not header_locked:
                            candidate = _find_column_indices([str(c or "") for c in row])
                            if (
                                candidate["date"] is not None
                                and candidate["description"] is not None
                                and (candidate["debit"] is not None or candidate["credit"] is not None or candidate["amount"] is not None)
                            ):
                                global_col_idx = candidate
                                header_locked = True
                                logger.info("Page %d table %d: header at row %d → %s",
                                            page_num, t_idx, row_idx, global_col_idx)
                                continue

                        if not header_locked:
                            continue

                        tx = _row_to_transaction(row, global_col_idx)
                        if tx:
                            transactions.append(tx)

    except Exception as exc:
        exc_repr = repr(exc)
        exc_str = str(exc)
        if "PasswordError" in exc_repr or "PDFPasswordIncorrect" in exc_repr or "invalid password" in exc_str.lower():
            logger.warning("PDF requires a password or provided password was incorrect.")
            raise ValueError("This PDF is password-protected. Please provide the correct password to upload it.") from exc
        
        logger.error("PDF parsing failed: %s", exc, exc_info=True)
        raise ValueError(f"Could not parse PDF: {exc}") from exc

    logger.info("PDF parsing complete: %d transactions extracted", len(transactions))
    return transactions

