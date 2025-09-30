from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agent.orchestrator import MomentumAgent

app =FastAPI(
    title="Momentum Agent API",
    description="API to control Momentum",
    version="1.0.0"
)

class AgentRequest(BaseModel):
    prompt: str

def run_agent_task(prompt: str):
    print("Background task started: Intialising agent...")
    agent = MomentumAgent()
    if agent.state_machine.get_state() != "ERROR":
        agent.run(prompt)
    else:
        print("Agent failed to initialised, skipping run...")

@app.post("/agent/run", status_code=202)
async def start_agent_run(request: AgentRequest, background_tasks: BackgroundTasks):
    print(f"Recieved API request with prompt: {request.prompt}")
    background_tasks.add_task(run_agent_task, request.prompt)
    return{"message": "Agent run intiated successfully.", "prompt": request.prompt}

@app.get("/")
def read_root():
    return {"status": "Momentum Agent API is running...."}