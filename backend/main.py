import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
sys.path.append('src')
from config.config_loader import ConfigLoader

app = FastAPI(
    title="Momentum API",
    description="An autonomous agent to translate business requirements to code.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration
config_loader = ConfigLoader()

class AgentRequest(BaseModel):
    prompt: str

@app.get("/", tags=["Check..."])
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Orchestrator is running"}

@app.get("/config", tags=["Config"])
async def get_config():
    """
    Test endpoint to verify configuration loading.
    """
    return {
        "status": "ok",
        "config": {
            "llm_model": config_loader.get("models.llm.name"),
            "embedding_model": config_loader.get("models.embedding.name"),
            "vector_db_path": config_loader.get("vector_db.path"),
            "max_tokens": config_loader.get("models.llm.max_tokens"),
            "temperature": config_loader.get("models.llm.temperature")
        }
    }

@app.post("/agent/run", tags=["Agent"])
async def run_agent(request: AgentRequest):
    """
    Run the agent with the given prompt.
    """
    return {
        "status": "success",
        "message": f"Agent processing: {request.prompt}",
        "task_id": "mock-task-123",
        "config_used": {
            "llm_model": config_loader.get("models.llm.name"),
            "max_tokens": config_loader.get("models.llm.max_tokens")
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)