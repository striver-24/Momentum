import os
import requests
from dotenv import load_dotenv
from ..config.config_loader import get_model_config

load_dotenv()

class LlamaConnector:
    def __init__(self):
        self.api_url = os.getenv("CEREBRAS_API_URL")
        self.api_key = os.getenv("CEREBRAS_API_KEY")
        if not self.api_url or not self.api_key:
            raise ValueError("CEREBRAS_API_URL and CEREBRAS_API_KEY must be set in .env")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Load LLM configuration
        self.llm_config = get_model_config('llm')

    def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.llm_config['name'],
            "prompt": prompt,
            "max_tokens": self.llm_config['max_tokens'],
            "temperature": self.llm_config['temperature']
        }

        try:
            print("Sending request to Cerebras API...")
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.llm_config['timeout']
            )
            response.raise_for_status()

            gen_text = response.json().get("choices")[0].get("text")
            print("Received response from Cerebras API.")
            return gen_text.strip()
        
        except requests.exceptions.RequestException as e:
            error_message = f"Error communicating with Cerebras API: {e}"
            print(error_message)
            return error_message

    def generate_plan(self, user_prompt: str) -> str:
        """Legacy method for backward compatibility"""
        from ..config.config_loader import get_prompt_template
        
        planning_prompt = get_prompt_template('planning')
        full_prompt = f"{planning_prompt['system']}\n\n{planning_prompt['template'].format(task=user_prompt)}"
        
        return self.generate_text(full_prompt)