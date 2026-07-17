import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.orchestrator.graph import graph
from app.memory.manager import MemoryManager
import uuid

load_dotenv()

app = FastAPI(title="Agent Orchestration System", description="Multi-agent orchestration platform")

class TaskRequest(BaseModel):
    task: str

@app.post("/api/task")
async def run_task(req: TaskRequest):
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    task_id = str(uuid.uuid4())
    memory_manager = MemoryManager(task_id=task_id)
    
    # Execute graph
    initial_state = {
        "messages": [],
        "original_task": req.task,
        "plan": {"subtasks": []},
        "current_subtask_id": "",
        "escalate_to_human": False,
        "final_output": "",
        "sender": "user",
        "current_task_id": task_id # pass to supervisor
    }
    
    # Save initial short-term memory
    memory_manager.save_working_memory(initial_state)
    
    result = graph.invoke(initial_state)
    
    # Update working memory
    memory_manager.save_working_memory(result)
    
    # If completed, extract lessons and save to long-term memory
    # In a real app, an agent would summarize this. For now, we mock it.
    summary = f"Task completed with plan: {result.get('plan')}"
    memory_manager.save_long_term_memory(
        task_description=req.task,
        execution_summary=summary,
        lessons_learned="Tools worked successfully."
    )
    memory_manager.clear_working_memory()
    
    return {"status": "success", "task_id": task_id, "task": req.task, "plan": result.get("plan")}

@app.get("/api/memory")
def get_memories(query: str):
    manager = MemoryManager(task_id="default")
    return {"results": manager.query_long_term_memory(query)}
    
@app.delete("/api/memory")
def delete_memory():
    # Example delete endpoint
    manager = MemoryManager(task_id="default")
    if manager.vector_store:
        manager.vector_store.delete_collection()
    return {"status": "success", "message": "Memory cleared"}
    
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
