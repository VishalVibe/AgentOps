from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from app.orchestrator.state import AgentState, Plan, SubTask
from app.memory.manager import MemoryManager
import uuid
import os

class SubTaskModel(BaseModel):
    description: str = Field(description="Description of the subtask")
    assigned_specialist: str = Field(description="One of: research, data, writing, execution")
    required_inputs: List[str] = Field(description="List of information required from previous subtasks or context")
    expected_output_format: str = Field(description="Format of the output (e.g., JSON, markdown, raw text)")

class PlanModel(BaseModel):
    subtasks: List[SubTaskModel]

def get_llm():
    # Helper to get the groq model
    return ChatGroq(model_name="llama3-70b-8192") # Or appropriate model

def supervisor_node(state: AgentState) -> dict:
    llm = get_llm()
    
    # Retrieve past memories for planning
    memory_manager = MemoryManager(task_id=state.get("current_task_id", "default"))
    past_memories = memory_manager.query_long_term_memory(state["original_task"])
    memory_context = "\n".join(past_memories) if past_memories else "No relevant past memories found."
    
    system_prompt = (
        "You are the Supervisor Agent. Your job is to decompose a complex task into an ordered list of subtasks. "
        "Assign each subtask to a specialist agent (research, data, writing, execution). "
        "Each subtask should clearly state its dependencies.\n\n"
        f"Relevant Past Execution Memories:\n{memory_context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Original Task: {task}\nCreate an execution plan.")
    ])
    
    chain = prompt | llm.with_structured_output(PlanModel)
    
    plan_data = chain.invoke({"task": state["original_task"]})
    
    # Convert Pydantic model to TypedDict matching our state
    subtasks_list = []
    for st in plan_data.subtasks:
        subtasks_list.append(SubTask(
            id=str(uuid.uuid4()),
            description=st.description,
            assigned_specialist=st.assigned_specialist,
            required_inputs=st.required_inputs,
            expected_output_format=st.expected_output_format,
            status="pending",
            result=None
        ))
        
    return {
        "plan": Plan(subtasks=subtasks_list),
        "sender": "supervisor"
    }
