from dataclasses import dataclass, field
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect


@dataclass(frozen=True)
class WSConnection:
    websocket: WebSocket
    user_id: UUID | None


@dataclass
class WSConnectionList:
    all: list[WSConnection] = field(default_factory=list)

    def get_websocket(self, user_id: UUID) -> WebSocket | None:
        for conn in self.all:
            if conn.user_id == user_id:
                return conn.websocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: WSConnectionList = WSConnectionList()

    async def connect(self, connection: WSConnection) -> None:
        self.active_connections.all.append(connection)

    def disconnect(self, connection: WSConnection) -> None:
        # добавить возможность дисконнектить по одному user_id или вебсокету
        self.active_connections.all.remove(connection)

    def get_ws(self, user_id: UUID) -> WebSocket:
        ws = self.active_connections.get_websocket(user_id)
        if not ws:
            print('Websocket not found!')
        return ws

    async def send_message(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        for conn in self.active_connections.all:
            await conn.websocket.send_json(message)

    async def get_online(self) -> int:
        return len(self.active_connections.all)



