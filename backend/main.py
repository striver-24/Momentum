import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="Momentum API",
    description="An autonomous agent to translate business requirements to code.",
    version="1.0.0"
)

@app.get("/", tags=["Check..."])
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Orchestrator is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)