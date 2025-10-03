import time
import os
import uuid
from dotenv import load_dotenv
from .state_machine import AgentState, AgentStateMachine
from ..connectors.llm_connector import LlamaConnector
from ..connectors.docker_connector import DockerConnector
from ..connectors.git_connector import GitConnector
from ..connectors.github_connector import GithubConnector

load_dotenv()

class MomentumAgent:
    def __init__(self, websocket_manager=None):
        self.state_machine = AgentStateMachine()
        self.websocket_manager = websocket_manager
        self.workspace_dir = None
        self.plan = ""
        self.feature_branch = ""
        self.pull_request_info = {}
        self.review_comments = []
        self.fix_attempts = 0
        self.max_fix_attempts = 3

        try:
            self.llm_connector = LlamaConnector()
            self.docker_connector = DockerConnector()
            self.github_connector = GithubConnector()
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

        while curr_state not in [AgentState.DONE, AgentState.ERROR]:
            try:
                await self.execute_state(curr_state, user_prompt)
            except Exception as e:
                print(f"An error occured in state {curr_state.name}: {e}")
                await self.broadcast_status("ERROR", f"Failed in state {curr_state.name}: {e}")
                self.state_machine.set_state(AgentState.ERROR)

            curr_state = self.state_machine.get_state()
        
        print(f"Agent run finished with state: {curr_state.name}")
        await self.broadcast_status("DONE", "Workflow complete.")

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
            self.workspace_dir = self.git_connector.clone_repo()

            self.feature_branch = f"feature/momentum-{uuid.uuid4().hex[:6]}"
            await self.broadcast_status(state_name, f"Creating new branch: {self.feature_branch}")
            self.git_connector.create_branch(self.feature_branch)

            await self.broadcast_status(state_name, "Thinking! Generating a plan...")
            plan_prompt = f"You are an expert software engineer. Create a concise, step-by-step plan to accomplish the following task. For each step, specify the file to be created or modified. Task: {prompt}"
            self.plan = self.llm_connector.generate_text(plan_prompt)
            await self.broadcast_status(state_name, f"Generated Plan:\n{self.plan}")
            self.state_machine.set_state(AgentState.CODE_GENERATION)

        elif state == AgentState.CODE_GENERATION:
            await self.broadcast_status(state_name, "Starting up isolated Docker environment...")
            self.docker_connector.start_container(self.workspace_dir)

            await self.broadcast_status(state_name, "Beginning dynamic code generation...")
            
            code_gen_prompt = f"""Based on the following plan, please write the Python code for the primary feature.
            
            **Plan:**
            {self.plan}

            **Task:** Write the full code for the main Python file. Do not write tests yet.
            Only output the raw, complete Python code. Do not include any explanations or markdown formatting.
            """
            
            await self.broadcast_status(state_name, "Asking LLM to generate production code...")
            generated_code = self.llm_connector.generate_text(code_gen_prompt)
            
            if not generated_code:
                raise Exception("LLM failed to generate production code.")

            file_path = "src/new_feature.py" 
            await self.broadcast_status(state_name, f"Writing generated code to: {file_path}")
            self.docker_connector.write_file_to_container(file_path, generated_code)
            
            self.state_machine.set_state(AgentState.TESTING)

        elif state == AgentState.TESTING:
            await self.broadcast_status(state_name, "Beginning dynamic test generation...")
            
            file_path = "src/new_feature.py"
            code_to_test = self.docker_connector.read_file_from_container(file_path)

            if not code_to_test:
                 raise Exception(f"Could not read file {file_path} to generate tests.")

            file_extension = os.path.splitext(file_path)[1]
            
            lang_details_map = {
                '.py': ('Python', 'pytest', 'python'),
                '.js': ('JavaScript', 'Jest', 'javascript'),
                '.ts': ('TypeScript', 'Jest', 'typescript'),
                '.java': ('Java', 'JUnit', 'java'),
                '.go': ('Go', "Go's native testing package", 'go'),
                '.rb': ('Ruby', 'RSpec', 'ruby')
            }
            language_name, test_framework, markdown_lang = lang_details_map.get(file_extension, ('the specified language', 'a common testing framework', ''))

            test_gen_prompt = f"""You are a quality assurance engineer. Given the following {language_name} code, please write a test file using `{test_framework}` to verify its functionality.

            **Code to Test:**
            ```{markdown_lang}
            {code_to_test}
            ```

            Only output the raw, complete code for the test file. Do not include any explanations or markdown formatting. Assume the necessary testing libraries are installed.
            """
            
            await self.broadcast_status(state_name, f"Asking LLM to generate {test_framework} tests...")
            generated_test = self.llm_connector.generate_text(test_gen_prompt)

            if not generated_test:
                raise Exception("LLM failed to generate test code.")

            test_path = "tests/test_new_feature.py"
            await self.broadcast_status(state_name, f"Writing generated test to: {test_path}")
            self.docker_connector.write_file_to_container(test_path, generated_test)

            await self.broadcast_status(state_name, f"Running dynamically generated tests with {test_framework}...")
            test_command = "pytest"
            exit_code, output = self.docker_connector.run_command(test_command)

            if exit_code == 0:
                await self.broadcast_status(state_name, "All generated tests passed!")
                self.state_machine.set_state(AgentState.AWAITING_REVIEW)
            else:
                raise Exception(f"Dynamically generated tests failed:\n{output.decode('utf-8')}")

        elif state == AgentState.AWAITING_REVIEW:
            if not self.pull_request_info:
                await self.broadcast_status(state_name, "Committing changes and pushing to remote repo...")
                self.git_connector.commit_and_push("feat: Implement new feature via Momentum Agent", self.feature_branch)
                await self.broadcast_status(state_name, f"Changes pushed to branch {self.feature_branch}")
                
                await self.broadcast_status(state_name, "Creating Pull Request...")
                self.pull_request_info = self.github_connector.create_pull_request(self.feature_branch, "main", "New Feature by Momentum", "This PR was auto-generated by the Momentum AI agent.")
                await self.broadcast_status(state_name, f"Pull Request created: {self.pull_request_info.get('html_url')}")

            await self.broadcast_status(state_name, "Waiting for CodeRabbitAI review... (will check for 5 mins)")
            self.review_comments = self.github_connector.get_pr_review_comments(self.pull_request_info['number'])

            if self.review_comments:
                await self.broadcast_status(state_name, f"Found {len(self.review_comments)} comments. Transitioning to FIXING.")
                self.state_machine.set_state(AgentState.FIXING)
            else:
                await self.broadcast_status(state_name, "No review comments found. All done!")
                self.state_machine.set_state(AgentState.DONE)

        elif state == AgentState.FIXING:
            if self.fix_attempts >= self.max_fix_attempts:
                raise Exception("Maximum fix attempts reached. Halting to prevent infinite loop.")
            
            self.fix_attempts += 1
            await self.broadcast_status(state_name, f"Starting self-correction attempt #{self.fix_attempts}...")

            target_file = "src/new_feature.py" 
            file_extension = os.path.splitext(target_file)[1]

            lang_map = {
                '.py': ('Python', 'python'),
                '.js': ('JavaScript', 'javascript'),
                '.ts': ('TypeScript', 'typescript'),
                '.java': ('Java', 'java'),
                '.go': ('Go', 'go'),
                '.rb': ('Ruby', 'ruby'),
                '.html': ('HTML', 'html'),
                '.css': ('CSS', 'css'),
            }
            language_name, markdown_lang = lang_map.get(file_extension, ('code', ''))

            combined_feedback = "\n".join([comment['body'] for comment in self.review_comments])

            await self.broadcast_status(state_name, f"Reading original code from {target_file}...")
            original_code = self.docker_connector.read_file_from_container(target_file)

            if not original_code:
                raise Exception(f"Could not read the file {target_file} to apply fixes.")

            fixer_prompt = f"""The following {language_name} code has issues that need to be fixed.

**Original Code:**
```{markdown_lang}
{original_code}
```

**Review Feedback:**
```
{combined_feedback}
```

Please rewrite the entire {language_name} file to address all the feedback points mentioned in the review.
Only provide the complete, corrected {language_name} code. Do not include any explanations or apologies.
"""

            await self.broadcast_status(state_name, "Asking LLM to generate corrected code...")
            corrected_code = self.llm_connector.generate_text(fixer_prompt)

            if not corrected_code:
                raise Exception("LLM failed to generate a corrected version of the code.")

            await self.broadcast_status(state_name, "Applying fixes...")
            self.docker_connector.write_file_to_container(target_file, corrected_code)

            await self.broadcast_status(state_name, "Committing and pushing the code fixes...")
            commit_message = f"fix: Address review comments (Attempt #{self.fix_attempts})"
            self.git_connector.commit_and_push(commit_message, self.feature_branch)

            self.review_comments = []
            await self.broadcast_status(state_name, "Fixes pushed. Returning to AWAITING_REVIEW state.")
            self.state_machine.set_state(AgentState.AWAITING_REVIEW)

        else:
            print(f"Unhandled state: {state_name}")
            self.state_machine.set_state(AgentState.DONE)
