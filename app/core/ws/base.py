import json
from typing import Any, Callable, Awaitable, Protocol
from abc import ABCMeta, abstractmethod

from fastapi import WebSocket
from starlette import status
from starlette.types import Message

from .manager import ConnectionManager, WSConnection


class ConnDataAwaitable(Protocol):
    def __call__(self, connection: WSConnection, data: Any) -> Awaitable:
        ...


class WebSocketEndpoint:
    __metaclass__ = ABCMeta
    encoding: str | None = None     # "text", "bytes", or "json".

    @abstractmethod
    async def dispatch(self, connection: WSConnection) -> None:
        """ Override to handle websocket interactions """

    @abstractmethod
    async def on_connect(self, connection: WSConnection) -> None:
        """ Override to handle an incoming websocket connection """
        await connection.websocket.accept()

    @abstractmethod
    async def on_receive(self, connection: WSConnection, data: Any) -> None:
        """ Override to handle an incoming websocket message """

    @abstractmethod
    async def on_disconnect(self, connection: WSConnection, close_code: int) -> None:
        """ Override to handle a disconnecting websocket """

    async def decode(self, websocket: WebSocket, message: Message) -> Any:
        if self.encoding == "text":
            if "text" not in message:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected text websocket messages, but got bytes")
            return message["text"]

        elif self.encoding == "bytes":
            if "bytes" not in message:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected bytes websocket messages, but got text")
            return message["bytes"]

        elif self.encoding == "json":
            if message.get("text") is not None:
                text = message["text"]
            else:
                text = message["bytes"].decode("utf-8")

            try:
                return json.loads(text)
            except json.decoder.JSONDecodeError:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Malformed JSON data received.")

        assert (
            self.encoding is None
        ), f"Unsupported 'encoding' attribute {self.encoding}"
        return message["text"] if message.get("text") else message["bytes"]


class WebSocketActions(WebSocketEndpoint):

    actions: list[str] = []
    manager = ConnectionManager()

    async def action_not_allowed(self, connection: WSConnection, data: Any) -> None:
        await self.manager.send_message(connection.websocket, {'action': 'Not allowed'})

    async def dispatch(self, connection: WSConnection) -> None:
        await self.on_connect(connection)
        close_code = status.WS_1000_NORMAL_CLOSURE
        try:
            while True:
                message = await connection.websocket.receive()
                if message['type'] == 'websocket.receive':
                    data = await self.decode(connection.websocket, message)
                    print(f'{data = }')
                    print(f'{type(data) = }')
                    if data['action'] not in self.actions:
                        await self.action_not_allowed(connection, data)
                        continue
                    await self.on_receive(connection, data)
                elif message['type'] == 'websocket.disconnect':
                    close_code = int(message.get('code') or status.WS_1000_NORMAL_CLOSURE)
                    break
        except Exception as exc:
            close_code = status.WS_1011_INTERNAL_ERROR
            raise exc
        finally:
            await self.on_disconnect(connection, close_code)

    async def on_connect(self, connection: WSConnection) -> None:
        # await connection.websocket.accept()
        await self.manager.connect(connection)

    async def on_receive(self, connection: WSConnection, data: Any) -> None:
        # handler: Callable[[WSConnection, Any], Awaitable] = getattr(self, data['action'], self.action_not_allowed)
        handler: ConnDataAwaitable = getattr(self, data['action'], self.action_not_allowed)
        print(f'{data["action"] = }')
        print(f'{handler.__name__ = }')
        return await handler(connection=connection, data=data)

    async def on_disconnect(self, connection: WSConnection, close_code: int) -> None:
        self.manager.disconnect(connection)
