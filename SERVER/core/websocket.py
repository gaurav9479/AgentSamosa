from fastapi import WebSocket
from typing import List, Dict, Any
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def broadcast_action(
        self, action: str, success: bool, data: Any = None, message: str = ""
    ):
        await self.broadcast({
            "type": "action_result",
            "action": action,
            "success": success,
            "data": data,
            "message": message,
        })

    async def broadcast_update(self, entity: str, operation: str, data: Any):
        await self.broadcast({
            "type": "data_update",
            "entity": entity,
            "operation": operation,
            "data": data,
        })


manager = ConnectionManager()
