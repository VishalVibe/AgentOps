import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.orchestrator.graph import graph

load_dotenv()

app = FastAPI(title="Agent Orchestration System", description="Multi-agent orchestration platform")

class TaskRequest(BaseModel):
    task: str

@app.post("/api/task")
async def run_task(req: TaskRequest):
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    # Execute graph
    initial_state = {
        "messages": [],
        "original_task": req.task,
        "plan": {"subtasks": []},
        "current_subtask_id": "",
        "escalate_to_human": False,
        "final_output": "",
        "sender": "user"
    }
    
    result = graph.invoke(initial_state)
    return {"status": "success", "task": req.task, "plan": result.get("plan")}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
