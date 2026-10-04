"""Deterministic fuzzy name matching for bank statement ownership."""

import re

# Match threshold for token-set ratio. 0.80 requires 80% overlap of tokens.
NAME_MATCH_THRESHOLD = 0.80

HONORIFICS = re.compile(
    r"\b(mr|mrs|ms|miss|dr|shri|smt|sh|s/o|d/o|w/o|c/o|m/s|sri)\b[.\s]*",
    re.IGNORECASE,
)

def normalize_name(name: str) -> set[str]:
    """Remove honorifics, lowercase, strip punctuation, return token set."""
    if not name:
        return set()
    name = HONORIFICS.sub("", name)
    name = re.sub(r"[^a-z\s]", "", name.lower())
    return set(name.split())

def token_set_ratio(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard-like: |intersection| / min(|set_a|, |set_b|) for inclusive matching."""
    if not set_a or not set_b:
        return 0.0
    
    intersection = 0
    # Handle initial matching (e.g., 'a' matches 'ankush')
    for a_tok in set_a:
        for b_tok in set_b:
            if a_tok == b_tok:
                intersection += 1
                break
            elif len(a_tok) == 1 and b_tok.startswith(a_tok):
                intersection += 1
                break
            elif len(b_tok) == 1 and a_tok.startswith(b_tok):
                intersection += 1
                break
                
    # We divide by the union or the smaller set?
    # To tolerate missing middle names, dividing by the smaller set size is better.
    # But to prevent "Dutta" matching "Ankush Kumar Dutta", we require at least 2 tokens.
    smaller_size = min(len(set_a), len(set_b))
    if smaller_size == 0:
        return 0.0
        
    return intersection / smaller_size

def name_matches(user_legal_name: str, statement_holder: str) -> bool:
    """
    Returns True if statement_holder is the same person as user_legal_name.
    A single shared token alone is NOT enough (guards against same-surname matches).
    """
    u_tokens = normalize_name(user_legal_name)
    s_tokens = normalize_name(statement_holder)
    
    if len(u_tokens) < 2 or len(s_tokens) < 2:
        return False  # single-word names are ambiguous; reject

    ratio = token_set_ratio(u_tokens, s_tokens)
    return ratio >= NAME_MATCH_THRESHOLD
