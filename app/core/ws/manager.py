from dataclasses import dataclass, field
from uuid import UUID
from typing import Any

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from app.config import config


@dataclass(frozen=True)
class WSConnection:
    """ Обертка для возможности идентификации пользователя по вебсокету """
    websocket: WebSocket
    user_id: UUID | None


@dataclass
class WSConnectionList:
    all: list[WSConnection] = field(default_factory=list)

    def get_websocket(self, user_id: UUID) -> WebSocket | None:
        """ Возвращает вебсокет по ID пользователя, если подключение открыто """
        for conn in self.all:
            if conn.user_id == user_id:
                return conn.websocket

    def get_websocket_list(self, user_ids: list[UUID]) -> list[WebSocket]:
        return [conn.websocket for conn in self.all if conn.user_id in user_ids]


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: WSConnectionList = WSConnectionList()

    async def connect(self, connection: WSConnection) -> None:
        if not config.DEBUG and self.active_connections.get_websocket(connection.user_id):
            await self.send_message(connection.websocket, {'action': 'already_connected'})
            return
        self.active_connections.all.append(connection)

    def disconnect(self, connection: WSConnection) -> None:
        if connection in self.active_connections.all:
            self.active_connections.all.remove(connection)

    def get_ws(self, user_id: UUID) -> WebSocket:
        ws = self.active_connections.get_websocket(user_id)
        if not ws:
            print('Websocket not found!')
        return ws

    async def send_message(self, websocket: WebSocket, message: Any) -> None:
        """ Отправляет сообщение конкретному пользователю """
        await websocket.send_json(jsonable_encoder(message))

    async def broadcast(self, message: Any) -> None:
        """ Отправляет сообщение всем подключенным пользователям """
        for conn in self.active_connections.all:
            await conn.websocket.send_json(jsonable_encoder(message))

    async def limited_broadcast(self, user_ids: list[UUID], message: Any) -> None:
        """ Отправляет сообщение группе пользователей """
        for ws in self.active_connections.get_websocket_list(user_ids):
            await ws.send_json(jsonable_encoder(message))

    async def get_online(self) -> int:
        """ Возвращает число текущих соединений """
        return len(self.active_connections.all)
