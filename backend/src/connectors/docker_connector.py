import docker
import io 
import tarfile
import os

class DockerConnector:
    """
    It will manage the connection with docker engine
    """
    def __init__(self):
        try:
            self.client = docker.from_env()
            print("Docker client initialised.")
        except docker.errors.DockerException as e:
            print(f"Error in initialising Docker: {e}")
            print("Make sure Docker is running")
            raise

    def create_container(self, image="python:3.10-slim"):
        """
        Create and starts new docker container
        """
        try:
            print(f"Creating new Docker container with image {image}")
            container = self.client.container.run(image, detach=True, tty=True)
            print(f"{container.short_id} container created")
            return container
        except docker.errors.ImageNotFound:
            print(f"Image {image} not found. Pulling from Docker Hub...")
            self.client.images.pull(image)
            container = self.client.containers.run(image, detach=True, tty=True)
            return container
        except docker.errors.APIError as e:
            print(f"Error in creating container: {e}")
            raise

    def execute_command(self, container, command: str):
        if not container:
            return -1, "Container doesn't exist"
        
        print(f"Executing command in container {container.short_id}: {command}")
        exit_code, output = container.exec_run(command)
        decoded_output = output.decode('utf-8').strip()
        print(f"Command executed with exit code {exit_code}. Output: {decoded_output}")
        return exit_code, decoded_output

    def cleanup_container(self, container):
        if not container:
            return

        try:
            print(f"Clearing container {container.short_id}")
            container.stop()
            container.remove()
            print(f"Container {container.short_id} cleared")
        except docker.errors.APIError as e:
            print(f"Error in cleaning up container: {e}")    