from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from ..agent.orchestrator import MomentumAgent
from .websocket_manager import ConnectionManager
from ..connectors.slack_connector import app_handler, slack_app
from ..config.config_loader import get_config

config = get_config()
api_config = config.get_section('api')

app = FastAPI()
manager = ConnectionManager()

origins = api_config['cors_origins']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def run_agent_and_notify(prompt: str):
    agent = MomentumAgent(websocket_manager=manager)
    await agent.run(prompt)

@app.get("/")
def read_root():
    return {"Status": "Momentum Backend is Running"}

@app.post(api_config['agent_run_endpoint'])
async def run_agent_endpoint(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    if not prompt:
        return PlainTextResponse("No prompt provided", status_code=400)
    
    asyncio.create_task(run_agent_and_notify(prompt))
    
    return {"message": "Agent run started. Connect to WebSocket for live updates."}

@app.websocket(api_config['websocket_endpoint'])
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)

@app.post(api_config['slack_events_endpoint'])
async def slack_events_endpoint(req: Request):
    return await app_handler.handle(req)

slack_config = config.get_section('slack')
@slack_app.command(slack_config['command'])
async def handle_slack_command_for_agent(ack, body, say, logger):
    prompt = body.get('text', '').strip()
    if prompt:
        logger.info(f"Triggering agent from Slack with prompt: {prompt}")
        asyncio.create_task(run_agent_and_notify(prompt))