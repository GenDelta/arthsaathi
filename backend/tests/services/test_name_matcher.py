import pytest
from app.services.name_matcher import name_matches, token_set_ratio, normalize_name
from app.services.statement_identity import extract_statement_identity

def test_normalize_name():
    assert normalize_name("Mr. Ankush Kumar") == {"ankush", "kumar"}
    assert normalize_name("MS. PRIYA S.") == {"priya", "s"}
    assert normalize_name("Dr.  John Doe  ") == {"john", "doe"}
    
def test_name_matches():
    # Exact match
    assert name_matches("Ankush Kumar", "Ankush Kumar") is True
    # Missing middle name but still matches (threshold >= 0.8)
    assert name_matches("Ankush Kumar Dutta", "Ankush Dutta") is True
    # Honorifics ignored
    assert name_matches("Ankush Kumar", "Mr. Ankush Kumar") is True
    assert name_matches("Ankush Kumar", "Shri Ankush Kumar") is True
    
    # Initials
    assert name_matches("Ankush K. Dutta", "Ankush Kumar Dutta") is True
    assert name_matches("A. K. Dutta", "Ankush Kumar Dutta") is True
    
    # Mismatch
    assert name_matches("Ankush Kumar", "Rahul Kumar") is False
    assert name_matches("Ankush Kumar", "Ankush Singh") is False
    assert name_matches("John Smith", "Jane Smith") is False

    # Single tokens rejected
    assert name_matches("Ankush", "Ankush") is False

def test_extract_statement_identity():
    # SBI-style
    text = "Account Name: Ankush Kumar Dutta\nAddress: 123 Main St\nAccount Number: 000000345678"
    identity = extract_statement_identity(text)
    assert "Ankush Kumar Dutta" in identity.holder_names
    assert identity.account_last4 == "5678"
    
    # HDFC-style
    text = "To,\nMR. ANKUSH KUMAR\nXYZ ROAD\nA/c No: ************1234\n"
    identity = extract_statement_identity(text)
    assert "MR. ANKUSH KUMAR" in identity.holder_names
    assert identity.account_last4 == "1234"
