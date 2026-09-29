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
    
    def extract_node(state: OnboardingState):
        if not state.get("messages"):
            return {"current_profile": state.get("current_profile", {})}
        
        last_msg = state["messages"][-1]
        if not isinstance(last_msg, HumanMessage) or not last_msg.content.strip():
            return {"current_profile": state.get("current_profile", {})}

        prompt = EXTRACTION_PROMPT.format(message=last_msg.content)
        
        # Many LLMs drop requests that only have a SystemMessage.
        # We send the extraction prompt as a HumanMessage to guarantee a response.
        llm = get_llm()
        res = llm.invoke([HumanMessage(content=prompt)])
        
        # Try to parse JSON from the response
        try:
            content = str(res.content)
            # Find JSON object in the response
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
        valid_fields = ["name", "employment_type", "occupation", "income_frequency", "average_income", "financial_pain_points"]
        for k, v in data.items():
            if v and k in valid_fields:
                new_profile[k] = v
                
        return {"current_profile": new_profile}

    def dialogue_node(state: OnboardingState):
        profile = state.get("current_profile", {})
        lang = state.get("language", "en")
        required_fields = ["name", "employment_type", "occupation", "income_frequency", "average_income", "financial_pain_points"]
        
        missing_fields = [f for f in required_fields if f not in profile or not profile[f]]
        
        if not missing_fields:
            completion_msg = (
                "Thank you! Your profile is complete. Taking you to your dashboard now! 🎉"
                if lang == "en"
                else "धन्यवाद! आपकी प्रोफ़ाइल पूरी हो गई है। अब आपको डैशबोर्ड पर ले जाया जा रहा है! 🎉"
            )
            return {"messages": [AIMessage(content=completion_msg)], "is_complete": True}
            
        next_field = missing_fields[0]
        prompt = DIALOGUE_SYSTEM_PROMPT.format(
            language=state.get("language", "en"),
            known_profile=json.dumps(profile, ensure_ascii=False),
            next_field=next_field
        )
        
        # Send system prompt + recent conversation history for context
        msgs = [SystemMessage(content=prompt)]
        if state.get("messages"):
            msgs.extend(state["messages"][-2:])
        else:
            # Many LLMs drop requests that only have a SystemMessage.
            # We kickstart the first message with a hidden prompt.
            msgs.append(HumanMessage(content="Start the conversation by warmly welcoming me to ArthSaathi and asking your first question." if lang == "en" else "मेरा ArthSaathi में स्वागत करते हुए बातचीत शुरू करें और अपना पहला प्रश्न पूछें।"))
            
        llm = get_llm()
        res = llm.invoke(msgs)
        
        return {"messages": [res], "is_complete": False}

    workflow = StateGraph(OnboardingState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("dialogue", dialogue_node)
    
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "dialogue")
    workflow.add_edge("dialogue", END)
    
    return workflow.compile()


onboarding_agent = build_onboarding_graph()
