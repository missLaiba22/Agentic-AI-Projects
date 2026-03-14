from langgraph.graph import StateGraph, START, END
from .state import ResearchState
from .nodes import research_node, writer_node

def create_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("research", research_node)
    workflow.add_node("writer", writer_node)

    workflow.add_edge(START, "research")
    workflow.add_edge("research", "writer")
    workflow.add_edge("writer", END)

    return workflow.compile()