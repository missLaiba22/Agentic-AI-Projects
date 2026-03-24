from langgraph.graph import StateGraph, END
from backend.models.debate_state import DebateState
from backend.agents.research_agent import researcher
from backend.agents.pro_agent import pro_arguer
from backend.agents.con_agent import con_arguer
from backend.agents.judge_agent import judge_arguments
from backend.session_store import get_checkpointer

checkpointer = get_checkpointer()

workflow = StateGraph(DebateState)
workflow.add_node("researcher", researcher)
workflow.add_node("pro_arguer", pro_arguer)
workflow.add_node("con_arguer", con_arguer)     
workflow.add_node("judge_arguments", judge_arguments)

workflow.set_entry_point("researcher")

# Fan-out: Research -> Pro and Con in parallel
workflow.add_edge("researcher", "pro_arguer")
workflow.add_edge("researcher", "con_arguer")

# Fan-in: Wait for both Pro and Con, then Judge
workflow.add_edge("pro_arguer", "judge_arguments")
workflow.add_edge("con_arguer", "judge_arguments")

workflow.add_edge("judge_arguments", END)

# Compile with SqliteSaver for persistence
debate_graph = workflow.compile(
    checkpointer=checkpointer, 
    interrupt_before=["judge_arguments"]  # Pause before judge for human review
)