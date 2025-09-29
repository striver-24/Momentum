import git
import os
import tempfile
from urllib.parse import urlparse

class GitConnector:
    """
    Manages git ops
    """
    def __init__(self, repo_url: str):
        self repo_url = repo_url
        self.local_path = tempfile.mkdtemp()
        self.repo = None
        print(f"Gitconnector initialised for : {self.repo_url}")
        print(f"local path : {self.local_path}")

    def clone_repo(self):
        try:
            print(f"Cloning {self.repo_url} in {self.local_path}")
            self.repo = git.Repo.clone_from(self.repo_url, self.local_path)
            print("Repository cloned successfully.")
            return True
        except git.exc.GitCommandError as e:
            print(f"Error cloning repository: {e}")
            return False
        
    def create_and_checkout_branch(self, branch_name: str):
        if not self.repo:
            print("Repo not cloned. Call clone_repo() first")
            return False
        
        try:
            print(f"Creating and checking out new branch : {bramch_name}")
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            print(f"Succesfully checked out to new branch: {branch_name}")
            return True
        except Exception as e:
            print(f"Error creating branch: {e}")
            return False
    
    def commit_changes(self, commit_message: str):
        if not self.repo:
            print("Repo not cloned")
            return False
        
        try:
            print("Staging all changes...")
            self.repo.git.add(A=True)
            print(f"Committing changes with message: {commit_message}")
            self.repo.index.commit(commit_message)
            print("Changes committed successfully.")
            return True
        except Exception as e:
            print(f"Error committing changes: {e}")
            return False
        
    def push_changes(self, branch_name: str):
        if not self.repo:
            print("Repo not cloned")
            return False
        
        try:
            print(f"Pushing changes to remote branch: {branch_name}")
            origin = self.repo.remote(name='origin')
            origin.push(refspec=f"{branch_name}:{branch_name}")
            print("Changes pushed successfully.")
            return True
        except Exception as e:
            print(f"Error pushing changes: {e}")
            return False