import json
from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> list of active WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Global broadcast connections (e.g., admin dashboard, active helpers)
        self.broadcast_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: int = None):
        await websocket.accept()
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
        else:
            self.broadcast_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int = None):
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if websocket in self.broadcast_connections:
            self.broadcast_connections.remove(websocket)

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        text = json.dumps(message)
        # Broadcast to all connected clients
        for connection in list(self.broadcast_connections):
            try:
                await connection.send_text(text)
            except Exception:
                pass
        for uid, connections in list(self.active_connections.items()):
            for connection in list(connections):
                try:
                    await connection.send_text(text)
                except Exception:
                    pass

ws_manager = ConnectionManager()
