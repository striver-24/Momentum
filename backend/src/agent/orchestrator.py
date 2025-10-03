import time
import os
import uuid
from dotenv import load_dotenv
from .state_machine import AgentState, AgentStateMachine
from ..connectors.llm_connector import LlamaConnector
from ..connectors.docker_connector import DockerConnector
from ..connectors.git_connector import GitConnector
from ..connectors.github_connector import GithubConnector
from ..config.config_loader import (
    get_config, get_agent_config, get_git_config, get_file_paths,
    get_language_config, get_prompt_template, get_status_message
)

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
        self.max_fix_attempts = get_agent_config()['max_fix_attempts']

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
                # Note: Cannot use await in __init__, will broadcast error during first run
                print("Error will be broadcast during agent run")

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
                await self.broadcast_status("ERROR", get_status_message('general', 'error').format(state=curr_state.name, error=e))
                self.state_machine.set_state(AgentState.ERROR)

            curr_state = self.state_machine.get_state()
        
        print(f"Agent run finished with state: {curr_state.name}")
        await self.broadcast_status("DONE", get_status_message('general', 'workflow_complete'))

        if self.workspace_dir:
            self.git_connector.cleanup()
        if self.docker_connector.container:
            self.docker_connector.stop_and_remove_container()
        
    async def execute_state(self, state: AgentState, prompt: str):
        state_name = state.name
        print(f"State executing: {state_name}")
        await self.broadcast_status(state_name, get_status_message('general', 'state_executing').format(state=state_name))

        if state == AgentState.PLANNING:
            await self.broadcast_status(state_name, get_status_message('planning', 'cloning'))
            self.workspace_dir = self.git_connector.clone_repo()

            git_config = get_git_config()
            self.feature_branch = f"{git_config['branch_prefix']}{uuid.uuid4().hex[:6]}"
            await self.broadcast_status(state_name, get_status_message('planning', 'creating_branch').format(branch=self.feature_branch))
            self.git_connector.create_branch(self.feature_branch)

            await self.broadcast_status(state_name, get_status_message('planning', 'generating_plan'))
            planning_prompt = get_prompt_template('planning')
            plan_prompt = f"{planning_prompt['system']}\n\n{planning_prompt['template'].format(task=prompt)}"
            self.plan = self.llm_connector.generate_text(plan_prompt)
            await self.broadcast_status(state_name, get_status_message('planning', 'plan_generated').format(plan=self.plan))
            self.state_machine.set_state(AgentState.CODE_GENERATION)

        elif state == AgentState.CODE_GENERATION:
            await self.broadcast_status(state_name, get_status_message('code_generation', 'starting_docker'))
            self.docker_connector.start_container(self.workspace_dir)

            await self.broadcast_status(state_name, get_status_message('code_generation', 'beginning_generation'))
            
            code_gen_template = get_prompt_template('code_generation')
            code_gen_prompt = code_gen_template.format(
                language="Python",
                plan=self.plan
            )
            
            await self.broadcast_status(state_name, get_status_message('code_generation', 'asking_llm'))
            generated_code = self.llm_connector.generate_text(code_gen_prompt)
            
            if not generated_code:
                raise Exception("LLM failed to generate production code.")

            file_path = get_file_paths()['default_code_file']
            await self.broadcast_status(state_name, get_status_message('code_generation', 'writing_file').format(file_path=file_path))
            self.docker_connector.write_file_to_container(file_path, generated_code)
            
            self.state_machine.set_state(AgentState.TESTING)

        elif state == AgentState.TESTING:
            await self.broadcast_status(state_name, get_status_message('testing', 'beginning_generation'))
            
            file_path = get_file_paths()['default_code_file']
            code_to_test = self.docker_connector.read_file_from_container(file_path)

            if not code_to_test:
                 raise Exception(f"Could not read file {file_path} to generate tests.")

            file_extension = os.path.splitext(file_path)[1]
            
            # Get language config based on file extension
            language_name = None
            test_framework = None
            markdown_lang = None
            
            config = get_config()
            for lang, lang_config in config.get_section('languages').items():
                if lang_config['extension'] == file_extension:
                    language_name = lang.title()
                    test_framework = lang_config['test_framework']
                    markdown_lang = lang_config['markdown_lang']
                    break
            
            if not language_name:
                language_name = 'the specified language'
                test_framework = 'a common testing framework'
                markdown_lang = ''

            test_gen_template = get_prompt_template('test_generation')
            test_gen_prompt = test_gen_template.format(
                language=language_name,
                test_framework=test_framework,
                markdown_lang=markdown_lang,
                code=code_to_test
            )
            
            await self.broadcast_status(state_name, get_status_message('testing', 'asking_llm').format(test_framework=test_framework))
            generated_test = self.llm_connector.generate_text(test_gen_prompt)

            if not generated_test:
                raise Exception("LLM failed to generate test code.")

            test_path = get_file_paths()['default_test_file']
            await self.broadcast_status(state_name, get_status_message('testing', 'writing_test').format(test_path=test_path))
            self.docker_connector.write_file_to_container(test_path, generated_test)

            # Get test command from language config
            test_command = "pytest"  # default fallback
            for lang, lang_config in config.get_section('languages').items():
                if lang_config['extension'] == file_extension:
                    test_command = lang_config['test_command']
                    break
            
            await self.broadcast_status(state_name, get_status_message('testing', 'running_tests').format(test_framework=test_framework))
            exit_code, output = self.docker_connector.run_command(test_command)

            if exit_code == 0:
                await self.broadcast_status(state_name, get_status_message('testing', 'tests_passed'))
                self.state_machine.set_state(AgentState.AWAITING_REVIEW)
            else:
                raise Exception(get_status_message('testing', 'tests_failed').format(output=output.decode('utf-8')))

        elif state == AgentState.AWAITING_REVIEW:
            if not self.pull_request_info:
                git_config = get_git_config()
                await self.broadcast_status(state_name, get_status_message('review', 'committing'))
                self.git_connector.commit_and_push(git_config['commit_messages']['feature'], self.feature_branch)
                await self.broadcast_status(state_name, get_status_message('review', 'pushed').format(branch=self.feature_branch))
                
                await self.broadcast_status(state_name, get_status_message('review', 'creating_pr'))
                pr_config = get_config().get_section('pull_request')
                self.pull_request_info = self.github_connector.create_pull_request(self.feature_branch, git_config['default_base_branch'], pr_config['title'], pr_config['body'])
                await self.broadcast_status(state_name, get_status_message('review', 'pr_created').format(url=self.pull_request_info.get('html_url')))

            await self.broadcast_status(state_name, get_status_message('review', 'waiting_review'))
            self.review_comments = self.github_connector.get_pr_review_comments(self.pull_request_info['number'])

            if self.review_comments:
                await self.broadcast_status(state_name, get_status_message('review', 'comments_found').format(count=len(self.review_comments)))
                self.state_machine.set_state(AgentState.FIXING)
            else:
                await self.broadcast_status(state_name, get_status_message('review', 'no_comments'))
                self.state_machine.set_state(AgentState.DONE)

        elif state == AgentState.FIXING:
            agent_config = get_agent_config()
            if self.fix_attempts >= agent_config['max_fix_attempts']:
                raise Exception("Maximum fix attempts reached. Halting to prevent infinite loop.")
            
            self.fix_attempts += 1
            await self.broadcast_status(state_name, get_status_message('fixing', 'starting_attempt').format(attempt=self.fix_attempts))

            target_file = get_file_paths()['default_code_file']
            file_extension = os.path.splitext(target_file)[1]

            # Get language config based on file extension
            language_name = "code"
            markdown_lang = ""
            
            config = get_config()
            for lang, lang_config in config.get_section('languages').items():
                if lang_config['extension'] == file_extension:
                    language_name = lang.title()
                    markdown_lang = lang_config['markdown_lang']
                    break

            combined_feedback = "\n".join([comment['body'] for comment in self.review_comments])

            await self.broadcast_status(state_name, get_status_message('fixing', 'reading_code').format(file=target_file))
            original_code = self.docker_connector.read_file_from_container(target_file)

            if not original_code:
                raise Exception(f"Could not read the file {target_file} to apply fixes.")

            fixer_template = get_prompt_template('code_fixing')
            fixer_prompt = fixer_template.format(
                language=language_name,
                markdown_lang=markdown_lang,
                original_code=original_code,
                feedback=combined_feedback
            )

            await self.broadcast_status(state_name, get_status_message('fixing', 'asking_llm'))
            corrected_code = self.llm_connector.generate_text(fixer_prompt)

            if not corrected_code:
                raise Exception("LLM failed to generate a corrected version of the code.")

            await self.broadcast_status(state_name, get_status_message('fixing', 'applying_fixes'))
            self.docker_connector.write_file_to_container(target_file, corrected_code)

            await self.broadcast_status(state_name, get_status_message('fixing', 'committing_fixes'))
            git_config = get_git_config()
            commit_message = git_config['commit_messages']['fix'].format(attempt=self.fix_attempts)
            self.git_connector.commit_and_push(commit_message, self.feature_branch)

            self.review_comments = []
            await self.broadcast_status(state_name, get_status_message('fixing', 'fixes_pushed'))
            self.state_machine.set_state(AgentState.AWAITING_REVIEW)

        else:
            print(f"Unhandled state: {state_name}")
            self.state_machine.set_state(AgentState.DONE)
