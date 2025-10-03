from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from ..agent.orchestrator import MomentumAgent
from .websocket_manager import ConnectionManager
from ..connectors.slack_connector import app_handler, slack_app

# --- App Initialization ---
app = FastAPI()
manager = ConnectionManager()

# --- CORS Middleware ---
# Allows the Next.js frontend to communicate with this backend
origins = ["*"] # In production, restrict this to your frontend's domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Agent Trigger Function ---
# Central function to run the agent and manage websockets
async def run_agent_and_notify(prompt: str):
    agent = MomentumAgent(websocket_manager=manager)
    await agent.run(prompt)

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"Status": "Momentum Backend is Running"}

@app.post("/agent/run")
async def run_agent_endpoint(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    if not prompt:
        return PlainTextResponse("No prompt provided", status_code=400)
    
    # Run the agent in the background
    asyncio.create_task(run_agent_and_notify(prompt))
    
    return {"message": "Agent run started. Connect to WebSocket for live updates."}

# --- WebSocket Endpoint ---
@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)

# --- NEW: Slack Events Endpoint ---
# This endpoint is the target for your Slack app's "Slash Commands" URL.
@app.post("/slack/events")
async def slack_events_endpoint(req: Request):
    return await app_handler.handle(req)

# This decorator listens for the command we defined in slack_connector.py
@slack_app.command("/momentum")
async def handle_slack_command_for_agent(ack, body, say, logger):
    # This function now only handles the agent triggering part
    prompt = body.get('text', '').strip()
    if prompt:
        # Run the agent in the background when triggered from Slack
        logger.info(f"Triggering agent from Slack with prompt: {prompt}")
        asyncio.create_task(run_agent_and_notify(prompt))