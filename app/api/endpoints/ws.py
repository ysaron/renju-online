import uuid
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query

from app.core.ws.base import WebSocketActions
from app.core.ws.manager import WSConnection
from app.api.services.games import GameService
from app.auth.deps import get_current_user_dependency
from app.models.user import User

router = APIRouter()
get_current_user = get_current_user_dependency(is_verified=True, websocket_mode=True)


class RenjuWSEndpoint(WebSocketActions):
    encoding = 'json'
    actions = ['create_game', 'start_game', 'join_game', 'ready', 'move', 'example']

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
async def renju(websocket: WebSocket, user: User = Depends(get_current_user)):
    await RenjuWSEndpoint().dispatch(websocket, user)
