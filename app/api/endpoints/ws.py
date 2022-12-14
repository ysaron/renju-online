import uuid
from typing import Any
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, WebSocket, Query
from pydantic import ValidationError

from app.core import exceptions
from app.core.db.deps import AsyncSession, get_async_session
from app.core.ws.base import WebSocketActions
from app.core.ws.manager import WSConnection
from app.api.services.games import GameService
from app.auth.deps import get_current_user_dependency
from app.auth.services import UserService
from app.models.user import User
from app.schemas.game import GameCreateSchema, GameSchemaOut, GameSchema, PlayerSchema, GameJoinSchema
from app.schemas import message
from app.enums.game import GameStateEnum, PlayerRoleEnum

router = APIRouter()
get_current_user = get_current_user_dependency(is_verified=True, websocket_mode=True)
async_session_context = asynccontextmanager(get_async_session)


class RenjuWSEndpoint(WebSocketActions):
    encoding = 'json'
    actions = ['create_game', 'start_game', 'join_game', 'ready', 'move', 'example']

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
                    message=message.OpenGameMessage(
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
        except exceptions.UnfinishedGame:
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail='You have an unfinished game. Finish it to start a new one.'),
            )
        except ValidationError as e:
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail=f'Cannot create new game: {e}'),
            )

    async def join_game(self, connection: WSConnection, data: Any) -> None:
        try:
            game_input_data = GameJoinSchema(id=uuid.UUID(data['game_id']))
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                game, role, reopen = await GameService(db).join_game(player=user, game_id=game_input_data.id)
                game_data = GameSchemaOut.from_orm(game)
                # открытие игры присоединившимся игроком
                await self.manager.send_message(
                    websocket=connection.websocket,
                    message=message.OpenGameMessage(
                        game=game_data,
                        my_role=role,
                    ),
                )
                if reopen:
                    # Игра открывается заново уже участвующим игроком, уведомлять всех не нужно
                    return

                # limited broadcast для игроков и зрителей игры
                await self.manager.limited_broadcast(
                    user_ids=[pr.player.id for pr in game.players],
                    message=message.PlayerJoinedMessage(
                        game=game_data,
                        player_name=user.name,
                        player_role=role,
                    ),
                )
                # уведомление всех и вся для обновления списка игр
                await self.manager.broadcast(message.PlayerJoinedListMessage(
                    game=game_data,
                    player_name=user.name,
                    player_role=role,
                ))
        except (ValidationError, ValueError, exceptions.NoGameFound):
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail='Invalid game ID'),
            )
        except exceptions.NoEmptySeats:
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail='All seats are occupied.'),
            )
        except exceptions.UnfinishedGame:
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail='You have an unfinished game. Finish it to start a new one.'),
            )
        except Exception as e:
            await self.manager.send_message(
                websocket=connection.websocket,
                message=message.ErrorMessage(detail=f'Unable to join the game. Please, try again later.'),
            )
            raise e     # log

    async def ready(self, connection: WSConnection, data: Any) -> None:
        try:
            game_input_data = GameJoinSchema(id=uuid.UUID(data['game_id']))
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                game, name, role = await GameService(db).set_player_ready(player=user, game_id=game_input_data.id)
                if not game:
                    return
                game_data = GameSchemaOut.from_orm(game)
                await self.manager.limited_broadcast(
                    user_ids=[pr.player.id for pr in game.players],
                    message=message.PlayerReadyMessage(
                        game=game_data,
                        player_name=name,
                        player_role=role,
                    ),
                )
                # --- попытка начать игру
                game = await GameService(db).attempt_to_start_game(game)
                if not game:
                    return

                game_data = GameSchemaOut.from_orm(game)
                current_player = game_data.current_player()
                if not current_player:
                    raise ValueError('Cannot determine current player')
                # для игроков и зрителей: игра началась - отразить на экране игры
                await self.manager.limited_broadcast(
                    user_ids=[pr.player.id for pr in game.players],
                    message=message.GameStartedMessage(game=game_data),
                )
                # для всех: игра началась - отразить в GameList
                await self.manager.broadcast(message=message.GameStartedListMessage(game=game_data))
                # для текущего игрока: разблокировать доску
                await self.manager.send_message(
                    websocket=self.manager.active_connections.get_websocket(user_id=current_player.player.id),
                    message=message.UnblockBoardMessage(game=game_data),
                )
        except (exceptions.UnsuitableGameState, exceptions.NotAPlayer):
            pass
        except (ValidationError, ValueError, exceptions.NoGameFound, exceptions.NotInGame) as e:
            # уведомляем об ошибке, выписываем игрока из игры без простановки поражения
            raise e
        except Exception as e:
            # log
            raise e


@router.websocket('/renju/ws')
async def renju(websocket: WebSocket, user: User = Depends(get_current_user)):
    await RenjuWSEndpoint().dispatch(websocket, user)
