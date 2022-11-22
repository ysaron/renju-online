from typing import Any
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, WebSocket, Query
from pydantic import ValidationError

from app.core.db.deps import AsyncSession, get_async_session
from app.core.ws.base import WebSocketActions
from app.core.ws.manager import WSConnection
from app.api.services.games import GameService
from app.auth.deps import get_current_user_dependency
from app.auth.services import UserService
from app.models.user import User
from app.schemas.game import GameCreateSchema, GameSchemaOut, GameSchema, PlayerSchema
from app.schemas import message
from app.enums.game import GameStateEnum, PlayerRoleEnum

router = APIRouter()
get_current_user = get_current_user_dependency(is_verified=True, websocket_mode=True)
async_session_context = asynccontextmanager(get_async_session)


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

    async def create_game(self, connection: WSConnection, data: Any) -> None:
        try:
            # валидация данных и создание игры
            game_data = GameCreateSchema(is_private=data.get('is_private', False), modes=data['modes'])
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                game = await GameService(db).create_game(creator=user, game_data=game_data)
                created_game_data = GameSchemaOut.from_orm(game)
                # открытие созданной игры
                await self.manager.send_message(
                    websocket=connection.websocket,
                    message=message.GameCreatedMessage(
                        game=created_game_data,
                        my_role=PlayerRoleEnum.first,
                    ),
                )
                # уведомление всех и вся о создании игры
                if all([
                    not created_game_data.is_private,
                    not created_game_data.with_myself,
                ]):
                    await self.manager.broadcast(message.GameAddedMessage(game=created_game_data))
        except ValidationError as e:
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail=f'Cannot create new game: {e}'),
            )


@router.websocket('/renju/ws')
async def renju(websocket: WebSocket, user: User = Depends(get_current_user)):
    await RenjuWSEndpoint().dispatch(websocket, user)
