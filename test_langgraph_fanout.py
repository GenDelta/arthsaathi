from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    val: Annotated[list, operator.add]

def node_a(state): return {"val": ["a"]}
def node_b(state): return {"val": ["b"]}
def node_c(state): return {"val": ["c"]}

workflow = StateGraph(State)
workflow.add_node("A", node_a)
workflow.add_node("B", node_b)
workflow.add_node("C", node_c)
workflow.add_edge(START, "A")
workflow.add_edge(START, "B")
workflow.add_edge("A", "C")
workflow.add_edge("B", "C")
app = workflow.compile()
print(app.invoke({"val": []}))

