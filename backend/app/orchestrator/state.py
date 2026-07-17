from typing import TypedDict, Annotated, Sequence, Any, List
from langchain_core.messages import BaseMessage
import operator

class SubTask(TypedDict):
    id: str
    description: str
    assigned_specialist: str
    required_inputs: List[str]
    expected_output_format: str
    status: str # "pending", "in_progress", "completed", "failed", "rejected"
    result: Any

class Plan(TypedDict):
    subtasks: List[SubTask]

def merge_messages(old: Sequence[BaseMessage], new: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    return list(old) + list(new)

def merge_plan(old_plan: Plan, new_plan: Plan) -> Plan:
    # A simple replacement for now, though we might want to update specific subtasks
    return new_plan if new_plan else old_plan

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    original_task: str
    plan: Annotated[Plan, merge_plan]
    current_subtask_id: str
    escalate_to_human: bool
    final_output: str
    sender: str # To track who sent the message (Supervisor, ResearchSpecialist, etc.)
