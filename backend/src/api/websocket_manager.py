from fastapi import WebSocket
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("WebSocket Client Connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("WebSocket Client Disconnected")

    async def broadcast(self, message: dict):
        print(f"Broadcasting message: {message}")
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message)) 