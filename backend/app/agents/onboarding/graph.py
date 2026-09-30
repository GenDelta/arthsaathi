"""Conversational Onboarding Agent — extracts user profile via natural dialogue."""

import json
from typing import TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.onboarding.prompts import DIALOGUE_SYSTEM_PROMPT, EXTRACTION_PROMPT
from app.core.llm import get_llm


class OnboardingState(TypedDict):
    messages: list
    current_profile: dict
    user_id: str
    language: str
    is_complete: bool


def build_onboarding_graph():
    """Build and compile the onboarding agent graph."""
    
    REQUIRED_FIELDS = ["name", "date_of_birth", "gender", "state_of_residence",
                       "employment_type", "occupation", "income_frequency",
                       "average_income", "financial_pain_points"]

    async def extract_node(state: OnboardingState):
        if not state.get("messages"):
            return {"current_profile": state.get("current_profile", {})}
        
        last_msg = state["messages"][-1]
        if not isinstance(last_msg, HumanMessage) or not last_msg.content.strip():
            return {"current_profile": state.get("current_profile", {})}

        # Compile recent history to provide context for short answers
        history_text = "\n".join([f"{'AI' if isinstance(m, AIMessage) else 'User'}: {m.content}" for m in state["messages"][-4:]])
        prompt = EXTRACTION_PROMPT.format(message=history_text)
        
        llm = get_llm(temperature=0.0)
        res = await llm.ainvoke([HumanMessage(content=prompt)])
        
        # Try to parse JSON from the response
        try:
            content = str(res.content)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
                print(f"DEBUG EXTR JSON: {data}")
            else:
                print(f"DEBUG EXTR NO JSON: {content}")
                data = {}
        except Exception as e:
            print(f"DEBUG EXTR ERR: {e} - content: {content}")
            data = {}
            
        new_profile = {**state.get("current_profile", {})}
        for k, v in data.items():
            if v and k in REQUIRED_FIELDS:
                new_profile[k] = v
                
        return {"current_profile": new_profile}

    async def dialogue_node(state: OnboardingState):
        profile = state.get("current_profile", {})
        lang = state.get("language", "en")
        
        missing_fields = [f for f in REQUIRED_FIELDS if f not in profile or not profile[f]]
        collected_fields = [f for f in REQUIRED_FIELDS if f in profile and profile[f]]
        
        # Hard stops: all fields collected OR conversation too long
        if not missing_fields or len(state.get("messages", [])) > 18:
            completion_msg = "Thank you! Your profile is complete. Taking you to your dashboard now! 🎉"
            return {"messages": [AIMessage(content=completion_msg)], "is_complete": True}
            
        next_field = missing_fields[0]
        prompt = DIALOGUE_SYSTEM_PROMPT.format(
            language=lang,
            known_profile=json.dumps(profile, ensure_ascii=False),
            collected_fields=", ".join(collected_fields) if collected_fields else "none yet",
            next_field=next_field
        )
        
        # Send system prompt + recent 4 messages for context
        msgs = [SystemMessage(content=prompt)]
        if state.get("messages"):
            msgs.extend(state["messages"][-4:])
        else:
            msgs.append(HumanMessage(content="Start the conversation by warmly welcoming me to ArthSaathi and asking your first question."))
            
        llm = get_llm()
        res = await llm.ainvoke(msgs)
        
        return {"messages": [res], "is_complete": False}

    workflow = StateGraph(OnboardingState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("dialogue", dialogue_node)
    
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "dialogue")
    workflow.add_edge("dialogue", END)
    
    return workflow.compile()


onboarding_agent = build_onboarding_graph()
