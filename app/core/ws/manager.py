from dataclasses import dataclass, field
from uuid import UUID
from typing import Any

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


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

    def get_websocket_list(self, user_ids: list[UUID]) -> list[WebSocket]:
        return [conn.websocket for conn in self.all if conn.user_id in user_ids]


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

    async def send_message(self, websocket: WebSocket, message: Any) -> None:
        await websocket.send_json(jsonable_encoder(message))

    async def broadcast(self, message: Any) -> None:
        """ Отправляет сообщение всем подключенным юзерам """
        for conn in self.active_connections.all:
            await conn.websocket.send_json(jsonable_encoder(message))

    async def limited_broadcast(self, user_ids: list[UUID], message: Any) -> None:
        """ Отправляет сообщение группе юзеров """
        for ws in self.active_connections.get_websocket_list(user_ids):
            await ws.send_json(jsonable_encoder(message))

    async def get_online(self) -> int:
        """ Возвращает число текущих соединений """
        return len(self.active_connections.all)



