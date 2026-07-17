from langgraph.graph import StateGraph, END
from app.orchestrator.state import AgentState
from app.orchestrator.agents.supervisor import supervisor_node
from app.orchestrator.agents.specialists import research_node, data_node, writing_node, execution_node
from app.orchestrator.agents.reviewer import reviewer_node

def route_from_supervisor(state: AgentState) -> str:
    # Find the first pending subtask
    for st in state.get("plan", {}).get("subtasks", []):
        if st["status"] == "pending":
            return st["assigned_specialist"]
    return END

def route_from_specialist(state: AgentState) -> str:
    # If escalated or failed, maybe we stop or go to a human node (Phase 3)
    if state.get("escalate_to_human"):
        return "human"
    return "reviewer"

def route_from_reviewer(state: AgentState) -> str:
    # Check the current subtask status
    current_subtask_id = state.get("current_subtask_id")
    current_subtask = None
    for st in state.get("plan", {}).get("subtasks", []):
        if st["id"] == current_subtask_id:
            current_subtask = st
            break
            
    if current_subtask and current_subtask["status"] == "rejected":
        return current_subtask["assigned_specialist"]
        
    # If completed, route to next specialist
    for st in state.get("plan", {}).get("subtasks", []):
        if st["status"] == "pending":
            return st["assigned_specialist"]
            
    return END

def human_node(state: AgentState) -> dict:
    # This node just acts as a placeholder where execution stops for human review.
    # In a full LangGraph Checkpointer setup, we'd interrupt here.
    return {"sender": "human"}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("research", research_node)
builder.add_node("data", data_node)
builder.add_node("writing", writing_node)
builder.add_node("execution", execution_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("human", human_node)

builder.set_entry_point("supervisor")

# Edges from supervisor
builder.add_conditional_edges("supervisor", route_from_supervisor, {
    "research": "research",
    "data": "data",
    "writing": "writing",
    "execution": "execution",
    END: END
})

# Edges from specialists to reviewer
for node in ["research", "data", "writing", "execution"]:
    builder.add_conditional_edges(node, route_from_specialist, {
        "reviewer": "reviewer",
        "human": "human",
        END: END
    })

# From human, we go to end (the API will resume by re-invoking with new state)
builder.add_edge("human", END)

# Edges from reviewer back to specialists or END
builder.add_conditional_edges("reviewer", route_from_reviewer, {
    "research": "research",
    "data": "data",
    "writing": "writing",
    "execution": "execution",
    END: END
})

graph = builder.compile()
