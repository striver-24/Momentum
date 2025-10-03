import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GithubConnector:
    """
    Will Handle comm with GitHub API
    """
    def __init__(self):
        self.github_token = os.getenv("GITHUB_PAT")
        self.repo_name = os.getenv("GITHUB_REPO_NAME")

        if not self.github_token or not self.repo_name:
            raise ValueError("github token and repo name must be set in .env file")
        
        self.api_base_url = f"https://api.github.com/repos/{self.repo_name}"
        self.headers = {
            "Authorisation" : f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        } 

    def create_pull_request(self, title: str, head_branch: str, base_branch: str = "main", body: str = " "):
        pr_url = f"{self.api_base_url}/pulls"
        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body if body else "This is an auto gen PR from MomentumAgent",
        }

        try:
            response = requests.post(pr_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            pr_data = response.json()
            print(f"Pull request created sucessfully!: {pr_data['html_url']}")
            return pr_data
        except requests.exceptions.RequestException as e:
            print(f"Error creating pull request: {e}")
            if e.response is not None:
                print(f"Response Body: {e.response.text}")
            return None