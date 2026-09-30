from typing import Annotated, Sequence, TypedDict
from operator import add
from langchain_core.messages import BaseMessage

class ArthSaathiState(TypedDict):
    """Global state definition for the Multi-Agent Supervisor."""
    messages: Annotated[Sequence[BaseMessage], add]
    user_id: str
    
    # Context injected from DB
    profile_context: dict[str, str]
    
    # Router outputs
    intent: str | None
    
    # Sub-agent outputs
    extracted_transaction: dict[str, str | float] | None
    flagged_entities: list[str]
    
    # Final safe output to return to user
    final_response: str | None
