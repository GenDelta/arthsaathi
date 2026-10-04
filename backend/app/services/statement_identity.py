"""Extract account holder identity from bank statement text."""

import re
from dataclasses import dataclass

HOLDER_PATTERNS = [
    re.compile(r"(?:account\s+holder|customer\s+name|account\s+name|name|name\s+of\s+customer)[:\s]+([A-Za-z\s\.]+)", re.IGNORECASE),
    re.compile(r"(?:in\s+favour\s+of|a/c\s+name)[:\s]+([A-Za-z\s\.]+)", re.IGNORECASE),
    # Common address block pattern:
    re.compile(r"^To[,\s]+\n([A-Z][A-Za-z\s\.]+)", re.MULTILINE),
]

ACCOUNT_PATTERNS = [
    re.compile(r"(?:account\s+(?:no|number|num))[:\s\.]+[xX*\-]*(\d{4,})", re.IGNORECASE),
    re.compile(r"a/c\s+no[:\s\.]+[xX*\-]*(\d{4,})", re.IGNORECASE),
]

@dataclass
class StatementIdentity:
    holder_names: list[str]
    account_last4: str | None

def extract_statement_identity(text: str) -> StatementIdentity:
    """
    Extract account holder name(s) and last 4 digits of account number
    from the text of a bank statement.
    """
    names = []
    last4 = None
    
    for pattern in HOLDER_PATTERNS:
        match = pattern.search(text)
        if match:
            # Clean up the matched name
            name = match.group(1).strip()
            # Stop if we hit a newline or multiple spaces indicating end of column
            name = re.split(r"  |\n", name)[0]
            if len(name) > 3:
                names.append(name)
                
    for pattern in ACCOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            acct = match.group(1).strip()
            last4 = acct[-4:] if len(acct) >= 4 else None
            break

    return StatementIdentity(holder_names=names, account_last4=last4)

import hmac
import hashlib
from app.core.config import get_settings

def compute_account_hmac(account_last4: str) -> str:
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, account_last4.encode(), hashlib.sha256).hexdigest()
