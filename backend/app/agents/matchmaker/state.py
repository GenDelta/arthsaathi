from typing import TypedDict, List, Dict, Any

class MatchmakerState(TypedDict):
    user_profile: Dict[str, Any]      # Extracted from SQLite user_profiles
    behavioral_summary: str           # From the blackboard
    central_candidates: List[Dict]
    state_candidates: List[Dict]
    final_schemes: List[Dict]

