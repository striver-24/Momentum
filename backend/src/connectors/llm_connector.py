import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Llmconnector:
    def __init__(self):
        self.api_url = os.getenv("CEREBRAS_API_URL")
        self.api_key = os.getenv("CEREBRAS_API_KEY")
        if not self.api_url or not self.api_key:
            raise ValueError("CEREBRAS_API_URL and CEREBRAS_API_KEY must be set in .env")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_plan(self, usr_prompt: str) -> str:
        system_prompt = (
            "You are an expert software engineer. Your task is to decompose a high-level "
            "business requirement into a detailed, step-by-step plan that a junior developer "
            "could follow. Each step should be a clear, actionable task. Do not generate the code, only the plan."
        )

        full_prompt = f"{system_prompt}\n\nRequirement: {usr_prompt}\n\nPlan:"

        payload = {
            "model" : "llama-4-maverick-17b-128e-instruct",
            "prompt": full_prompt,
            "max_tokens": 500,
            "temperature": 0.5
        }

        try:
            print("Sending request to Cerebras API...")
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()

            gen_text = response.json().get("choices")[0].get("text")
            print("Received response from Cerebras API.")
            return gen_text.strip()
        
        except requests.exceptions.RequestException as e:
            error_message = f"Error communicating with Cerebras API: {e}"
            print(error_message)
            return error_message