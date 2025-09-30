import time
import os
import uuid
from dotenv import load_dotenv
from .state_machine import AgentState, AgentStateMachine
from ..connectors.llm_connector import LLMConnector
from ..connectors.docker_connector import DockerConnector
from ..connectors.git_connector import GitConnector

load_dotenv()

class MomentumAgent:
    def __init__(self, websocket_manager=None):
        self.state_machine = AgentStateMachine()
        self.websocket_manager = websocket_manager
        self.workspace_dir = None
        self.plan= ""
        self.feature_branch = ""

        try:
            self.llm_connector = LLMConnector()
            self.docker_connector = DockerConnector()
            repo_url = os.getenv("GIT_REPO_URL")
            if not repo_url:
                raise ValueError("GIT_REPO_URL must be set in .env")
            self.git_connector = GitConnector(repo_url=repo_url)
        except Exception as e:
            print(f"Error initializing connectors: {e}")
            self.state_machine.set_state(AgentState.ERROR)
            if self.websocket_manager:
                self.websocket_manager.broadcast("ERROR!!!", f"initializing connectors: {e}")

    
    async def broadcast_status(self, state: str, message: str):
        if self.websocket_manager:
            payload = {"state": state, "message": message}
            await self.websocket_manager.broadcast(payload)

    async def run(self, user_prompt: str):
        curr_state = self.state_machine.get_state()
        print(f"Starting agent run from state: {curr_state}")

        while curr_state != AgentState.DONE and curr_state != AgentState.ERROR:
            try:
                await self.execute_state(curr_state, user_prompt)
            except Exception as e:
                print(f"An error occured in state {curr_state}: {e}")
                await self.broadcast_status("ERROR!!!", f"Failed in state {curr_state}: {e}")
                self.state_machine.set_state(AgentState.ERROR)

            curr_state = self.state_machine.get_state()
        
        print(f"Agent run finished with state: {curr_state}")
        if curr_state == AgentState.ERROR:
            await self.broadcast_status("DONE", "Workflow complete")

        if self.workspace_dir:
            self.git_connector.cleanup()
        if self.docker_connector.container:
            self.docker_connector.stop_and_remove_container()
        
    async def execute_state(self, state: AgentState, prompt: str):
        state_name = state.name
        print(f"State executing: {state_name}")
        await self.broadcast_status(state_name, f"State executing: {state_name}")

        if state == AgentState.PLANNING:
            await self.broadcast_status(state_name, "Cloning repository...")
