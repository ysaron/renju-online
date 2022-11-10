import uuid
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query

from app.core.ws.base import WebSocketActions
from app.core.ws.manager import WSConnection
from app.api.services.games import GameService

router = APIRouter()


class RenjuWSEndpoint(WebSocketActions):
    encoding = 'json'
    actions = ['create_game', 'start_game', 'join_game', 'ready', 'move', 'example']
    service = GameService()

    async def example(self, connection: WSConnection, data: Any) -> None:
        """  """
        await self.manager.broadcast(
            {
                'action': 'example',
                'data': data['data'],
                'online': await self.manager.get_online(),
            }
        )


@router.websocket('/renju/ws')
async def renju(websocket: WebSocket, token: str = Query(None, description='That Bearer token')):
    print(f'{token = }')
    user_id = uuid.uuid4()
    await RenjuWSEndpoint().dispatch(WSConnection(websocket, user_id))
