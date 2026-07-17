from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.orchestrator.state import AgentState
from app.orchestrator.tools import get_specialist_tools

def get_llm():
    return ChatGroq(model_name="llama3-70b-8192")

def specialist_node(state: AgentState, specialist_type: str) -> dict:
    llm = get_llm()
    tools = get_specialist_tools(specialist_type)
    
    system_prompt = f"You are a specialized {specialist_type} agent. You have access to tools to accomplish your task."
    
    # Check if there is an active subtask for this specialist
    current_subtask = None
    for st in state.get("plan", {}).get("subtasks", []):
        if st["status"] in ["pending", "rejected"] and st["assigned_specialist"] == specialist_type:
            current_subtask = st
            break
            
    if not current_subtask:
        return {"sender": specialist_type} # Nothing to do
        
    agent = create_react_agent(llm, tools=tools, state_modifier=system_prompt)
    
    # Execute the task
    input_str = f"Task: {current_subtask['description']}\nRequired Inputs: {current_subtask['required_inputs']}\nOutput Format: {current_subtask['expected_output_format']}"
    if current_subtask["status"] == "rejected":
        input_str += f"\nPrevious attempt rejected. Reason: {current_subtask.get('result')}"
    
    try:
        # Create a clean message list for the agent to avoid confusing it with the whole graph state
        result = agent.invoke({"messages": [("user", input_str)]})
        final_message = result["messages"][-1].content
        
        # Update the plan with the result
        new_plan = state["plan"].copy()
        for i, st in enumerate(new_plan["subtasks"]):
            if st["id"] == current_subtask["id"]:
                new_plan["subtasks"][i]["status"] = "completed"
                new_plan["subtasks"][i]["result"] = final_message
                
        return {
            "plan": new_plan,
            "sender": specialist_type,
            "current_subtask_id": current_subtask["id"] # Passing this to reviewer
        }
    except Exception as e:
        # Handle failure
        new_plan = state["plan"].copy()
        for i, st in enumerate(new_plan["subtasks"]):
            if st["id"] == current_subtask["id"]:
                new_plan["subtasks"][i]["status"] = "failed"
                new_plan["subtasks"][i]["result"] = str(e)
                
        return {
            "plan": new_plan,
            "sender": specialist_type,
            "escalate_to_human": True # Basic escalation on failure for now
        }

def research_node(state: AgentState) -> dict:
    return specialist_node(state, "research")

def data_node(state: AgentState) -> dict:
    return specialist_node(state, "data")

def writing_node(state: AgentState) -> dict:
    return specialist_node(state, "writing")

def execution_node(state: AgentState) -> dict:
    return specialist_node(state, "execution")
