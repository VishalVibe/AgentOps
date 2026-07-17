from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.orchestrator.state import AgentState

class ReviewResult(BaseModel):
    approved: bool = Field(description="Whether the output meets the requirements")
    feedback: str = Field(description="Feedback for the specialist if rejected, or reasoning if approved")

def get_llm():
    return ChatGroq(model_name="llama3-70b-8192")

def reviewer_node(state: AgentState) -> dict:
    llm = get_llm()
    
    current_subtask_id = state.get("current_subtask_id")
    if not current_subtask_id:
        return {"sender": "reviewer"}

    current_subtask = None
    for st in state.get("plan", {}).get("subtasks", []):
        if st["id"] == current_subtask_id:
            current_subtask = st
            break
            
    if not current_subtask or current_subtask["status"] != "completed":
        return {"sender": "reviewer"}
        
    system_prompt = (
        "You are the Reviewer Agent. Your job is to review the output of a specialist agent "
        "and determine if it meets the requirements of the subtask."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Subtask: {description}\nExpected Output Format: {expected_format}\nOutput: {output}\n\nReview this output.")
    ])
    
    chain = prompt | llm.with_structured_output(ReviewResult)
    
    review = chain.invoke({
        "description": current_subtask["description"],
        "expected_format": current_subtask["expected_output_format"],
        "output": current_subtask["result"]
    })
    
    new_plan = state["plan"].copy()
    for i, st in enumerate(new_plan["subtasks"]):
        if st["id"] == current_subtask_id:
            if review.approved:
                # Keep status as completed
                pass
            else:
                new_plan["subtasks"][i]["status"] = "rejected"
                new_plan["subtasks"][i]["result"] = f"Reviewer Feedback: {review.feedback}\nPrevious Output: {st['result']}"
                
    return {
        "plan": new_plan,
        "sender": "reviewer"
    }
