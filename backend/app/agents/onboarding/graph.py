import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Any
from app.agents.onboarding.prompts import EXTRACTION_PROMPT, DIALOGUE_SYSTEM_PROMPT
from app.agents.onboarding.schemas import ExtractionWithEvidence, ExtractedField
from app.core.llm import get_llm

class OnboardingState(TypedDict):
    messages: list
    current_profile: dict
    user_id: str
    language: str
    is_complete: bool

QUESTION_TEMPLATES = {
    "name": "What is your full name?",
    "legal_name": "What is your full name exactly as it appears on your bank statement?",
    "date_of_birth": "What is your date of birth or age?",
    "gender": "What is your gender?",
    "state_of_residence": "Which state of India do you live in?",
    "employment_type": "What type of work do you do? For example: salaried, gig work, farming.",
    "occupation": "What is your specific job or occupation?",
    "income_frequency": "How often do you receive your income? (daily, weekly, monthly, seasonal)",
    "average_income": "Roughly how much do you earn each cycle in rupees?",
    "financial_pain_points": "What is your biggest financial worry or goal right now?",
}
REQUIRED_FIELDS = list(QUESTION_TEMPLATES.keys())

async def extract_node(state: OnboardingState):
    last_msg = ""
    messages = state.get("messages", [])
    
    # Find last user message
    for i in range(len(messages)-1, -1, -1):
        if messages[i].type == "human":
            last_msg = messages[i].content
            break
            
    if not last_msg:
        return state

    # Infer the question asked based on the missing profile fields
    profile = state.get("current_profile") or {}
    missing_fields = [f for f in REQUIRED_FIELDS if not profile.get(f)]
    target_field = missing_fields[0] if missing_fields else "unknown"
    agent_msg = QUESTION_TEMPLATES.get(target_field, "Unknown question")
        
    prompt = EXTRACTION_PROMPT.format(agent_question=agent_msg, user_message=last_msg, target_field=target_field)
    
    with open("onboarding_debug.log", "a", encoding="utf-8") as debug_file:
        debug_file.write(f"\n{'='*50}\n=== NEW EXTRACTION ===\nPROMPT:\n{prompt}\n\n")
        
    try:
        raw_llm = get_llm(temperature=0.0)
        res = await raw_llm.ainvoke([HumanMessage(content=prompt)])
        text = res.content.strip()
        
        with open("onboarding_debug.log", "a", encoding="utf-8") as debug_file:
            debug_file.write(f"RAW LLM RESPONSE:\n{text}\n\n")
            
        if text.startswith("```"):
            text = __import__("re").sub(r"^```[a-zA-Z]*\n?", "", text).rstrip("`").strip()
            
        extracted = ExtractedField.model_validate_json(text)
        
        with open("onboarding_debug.log", "a", encoding="utf-8") as debug_file:
            debug_file.write(f"PARSED EXTRACTION:\n{extracted.model_dump_json(indent=2)}\n")
            
    except Exception as e:
        print(f"Extraction error: {e}")
        with open("onboarding_debug.log", "a", encoding="utf-8") as debug_file:
            debug_file.write(f"EXTRACTION CRASHED: {e}\n")
        return state
        
    new_profile = dict(state.get("current_profile") or {})
    
    if extracted and extracted.value is not None:
        evidence = extracted.evidence or ""
        if evidence.lower() in last_msg.lower():
            if target_field != "unknown" and not new_profile.get(target_field):
                new_profile[target_field] = extracted.value
                        
    return {"current_profile": new_profile}

async def dialogue_node(state: OnboardingState):
    profile = state.get("current_profile", {})
    missing_fields = [f for f in REQUIRED_FIELDS if not profile.get(f)]
    
    if not missing_fields or len(state["messages"]) >= 18:
        return {"messages": [AIMessage(content="Thank you! Your profile is complete. Taking you to your dashboard now! 🎉")], "is_complete": True}
        
    next_field = missing_fields[0]
    question = QUESTION_TEMPLATES[next_field]
    
    llm = get_llm(temperature=0.0)
    system_msg = DIALOGUE_SYSTEM_PROMPT.format(question_template=question)
    
    msgs = [SystemMessage(content=system_msg)]
    has_user = False
    if state["messages"]:
        last_user = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if last_user:
            msgs.append(HumanMessage(content=last_user.content))
            has_user = True
            
    if not has_user:
        msgs.append(HumanMessage(content="Hi, I am ready to start setting up my profile."))
        
    response = await llm.ainvoke(msgs)
    return {"messages": [response], "is_complete": False}

def build_onboarding_graph():
    workflow = StateGraph(OnboardingState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("dialogue", dialogue_node)
    
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "dialogue")
    workflow.add_edge("dialogue", END)
    
    return workflow.compile()

onboarding_agent = build_onboarding_graph()
