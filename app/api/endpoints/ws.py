import uuid
from typing import Any
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, WebSocket, Query
from pydantic import ValidationError

from app.config import config
from app.core import exceptions
from app.core.db.deps import AsyncSession, get_async_session
from app.core.ws.base import WebSocketActions
from app.core.ws.manager import WSConnection
from app.api.services.games import GameService
from app.auth.deps import get_current_user_dependency
from app.auth.services import UserService
from app.models.user import User
from app.schemas.game import GameCreateSchema, GameSchemaOut, GameJoinSchema, MoveInputSchema
from app.schemas import message
from app.enums.game import GameStateEnum, PlayerRoleEnum

router = APIRouter()
get_current_user = get_current_user_dependency(is_verified=True, websocket_mode=True)
async_session_context = asynccontextmanager(get_async_session)


class RenjuWSEndpoint(WebSocketActions):
    encoding = 'json'
    actions = ['create_game', 'join_game', 'ready', 'leave', 'move']

    async def create_game(self, connection: WSConnection, data: Any) -> None:
        try:
            # валидация данных и создание игры
            game_input_data = GameCreateSchema(is_private=data.get('is_private', False), modes=data['modes'])
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                game_meta = await GameService(db).create_game(creator=user, game_data=game_input_data)
                game_schema = GameSchemaOut.from_orm(game_meta.game)
                # открытие созданной игры
                await self.manager.send_message(
                    websocket=connection.websocket,
                    message=message.OpenGameMessage(
                        game=game_schema,
                        my_role=PlayerRoleEnum.first,
                    ),
                )
                # уведомление всех и вся о создании игры
                if all([
                    not game_schema.is_private,
                    not game_schema.with_myself,
                ]):
                    await self.manager.broadcast(message.GameAddedMessage(game=game_schema))
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
                game_meta = await GameService(db).join_game(player=user, game_id=game_input_data.id)
                game_schema = GameSchemaOut.from_orm(game_meta.game)
                # открытие игры присоединившимся игроком
                await self.manager.send_message(
                    websocket=connection.websocket,
                    message=message.OpenGameMessage(
                        game=game_schema,
                        my_role=game_meta.current_role,
                    ),
                )
                if game_meta.reopen:
                    # Игра открывается заново уже участвующим игроком, уведомлять всех не нужно
                    return

                # limited broadcast для игроков и зрителей игры
                await self.manager.limited_broadcast(
                    user_ids=[pr.player.id for pr in game_meta.game.players],
                    message=message.PlayerJoinedMessage(
                        game=game_schema,
                        player_name=user.name,
                        player_role=game_meta.current_role,
                    ),
                )
                # уведомление всех и вся для обновления списка игр
                await self.manager.broadcast(message.PlayerJoinedListMessage(
                    game=game_schema,
                    player_name=user.name,
                    player_role=game_meta.current_role,
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
                game_meta = await GameService(db).set_player_ready(player=user, game_id=game_input_data.id)
                if not game_meta.game:
                    return
                game_schema = GameSchemaOut.from_orm(game_meta.game)
                await self.manager.limited_broadcast(
                    user_ids=[pr.player.id for pr in game_meta.game.players],
                    message=message.PlayerReadyMessage(
                        game=game_schema,
                        player_name=game_meta.current_player_name,
                        player_role=game_meta.current_role,
                    ),
                )
                # --- попытка начать игру
                game = await GameService(db).attempt_to_start_game(game_meta.game)
                if not game:
                    return

                game_schema = GameSchemaOut.from_orm(game)
                current_player = game_schema.current_player()
                if not current_player:
                    raise ValueError('Cannot determine current player')
                # для игроков и зрителей: игра началась - отразить на экране игры
                await self.manager.limited_broadcast(
                    user_ids=[pr.player.id for pr in game.players],
                    message=message.GameStartedMessage(game=game_schema),
                )
                # для всех: игра началась - отразить в GameList
                await self.manager.broadcast(message=message.UpdateGameInListMessage(game=game_schema))
                # для текущего игрока: разблокировать доску
                await self.manager.send_message(
                    websocket=self.manager.active_connections.get_websocket(user_id=current_player.player.id),
                    message=message.UnblockBoardMessage(game=game_schema),
                )
        except (exceptions.UnsuitableGameState, exceptions.NotAPlayer):
            pass
        except (ValidationError, ValueError, exceptions.NoGameFound, exceptions.NotInGame) as e:
            # уведомляем об ошибке, выписываем игрока из игры без простановки поражения
            raise e
        except Exception as e:
            # log
            raise e

    async def leave(self, connection: WSConnection, data: Any) -> None:
        try:
            game_input_data = GameJoinSchema(id=uuid.UUID(data['game_id']))
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                game_meta = await GameService(db).leave(player=user, game_id=game_input_data.id)
                user_ids = [pr.player.id for pr in game_meta.game.players]

                game_schema = GameSchemaOut.from_orm(game_meta.game)

                # вернуть на главный экран вышедшего игрока
                await self.manager.send_message(
                    websocket=connection.websocket,
                    message=message.LeftGameMessage(game=game_schema)
                )

                if game_meta.delete:
                    await GameService(db).remove_game(game_meta.game)
                    # удаляем игру из GameList - для всех
                    await self.manager.broadcast(message.GameRemovedListMessage(game_id=game_input_data.id))
                    # выкидываем в главное меню - для участников
                    await self.manager.limited_broadcast(
                        user_ids=user_ids,
                        message=message.GameRemovedMessage(game_id=game_input_data.id),
                    )
                    return

                # для всех: отразить изменения в GameList (красный либо пустой индикатор)
                await self.manager.broadcast(message=message.UpdateGameInListMessage(game=game_schema))
                # для участников: отразить изменения в playerBlock (красный либо пустой блок, зависит от результата)
                await self.manager.limited_broadcast(
                    user_ids=user_ids,
                    message=message.UpdateGameMessage(game=game_schema),
                )

                if game_meta.game.state == GameStateEnum.finished:
                    # отображаем результат участникам
                    verbose_result = game_schema.verbose_result()
                    await self.manager.limited_broadcast(
                        user_ids=user_ids,
                        message=message.GameFinishedMessage(game=game_schema, result=verbose_result),
                    )

        except exceptions.NotAPlayer:
            pass
        except Exception as e:
            raise e

    async def move(self, connection: WSConnection, data: Any) -> None:
        try:
            game_input_data = GameJoinSchema(id=uuid.UUID(data['game_id']))
            move_input_data = MoveInputSchema(x=data['x'], y=data['y'])
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                move_meta = await GameService(db).move(player=user, cell=move_input_data, game_id=game_input_data.id)
                user_ids = [pr.player.id for pr in move_meta.game.players]
                game_schema = GameSchemaOut.from_orm(move_meta.game)
                await self.manager.limited_broadcast(
                    user_ids=user_ids,
                    message=message.MoveMessage(game=move_meta.game, move=move_meta.move),
                )
                if move_meta.game.state == GameStateEnum.pending:
                    current_player = game_schema.current_player()
                    print(f'{current_player.role = }')
                    await self.manager.send_message(
                        websocket=self.manager.active_connections.get_websocket(user_id=current_player.player.id),
                        message=message.UnblockBoardMessage(game=game_schema),
                    )
                if move_meta.game.state == GameStateEnum.finished:
                    verbose_result = game_schema.verbose_result()
                    await self.manager.limited_broadcast(
                        user_ids=user_ids,
                        message=message.GameFinishedMessage(
                            game=game_schema,
                            result=verbose_result,
                            winning_cells_coords=[cell.coord for cell in move_meta.winning_cells],
                        ),
                    )
                    await self.manager.broadcast(message=message.UpdateGameInListMessage(game=game_schema))
        except exceptions.FalseClick:
            pass
        except Exception as e:
            # Мб разблокировать снова борду для этого юзера? Он же не сделал ход, по идее.
            # Или мог?
            raise e

    async def on_disconnect(self, connection: WSConnection, close_code: int) -> None:
        await super().on_disconnect(connection, close_code)
        if config.DEBUG:
            return
        try:
            async with async_session_context() as db:
                user = await UserService(db).get_user_by_id(connection.user_id)
                game_service = GameService(db)
                active_games = await game_service.get_user_games(user, scope='unfinished')
                for game in active_games:
                    game_meta = await game_service.leave(player=user, game_id=game.id)
                    user_ids = [pr.player.id for pr in game_meta.game.players]
                    game_schema = GameSchemaOut.from_orm(game_meta.game)
                    if game_meta.delete:
                        await game_service.remove_game(game_meta.game)
                        # удаляем игру из GameList - для всех
                        await self.manager.broadcast(message.GameRemovedListMessage(game_id=game.id))
                        # выкидываем в главное меню - для участников
                        await self.manager.limited_broadcast(
                            user_ids=user_ids,
                            message=message.GameRemovedMessage(game_id=game.id),
                        )
                        return

                    # для всех: отразить изменения в GameList (красный либо пустой индикатор)
                    await self.manager.broadcast(message=message.UpdateGameInListMessage(game=game_schema))
                    # для участников: отразить изменения в playerBlock (красный либо пустой блок, зависит от результата)
                    await self.manager.limited_broadcast(
                        user_ids=user_ids,
                        message=message.UpdateGameMessage(game=game_schema),
                    )

                    if game_meta.game.state == GameStateEnum.finished:
                        # отображаем результат участникам
                        verbose_result = game_schema.verbose_result()
                        await self.manager.limited_broadcast(
                            user_ids=user_ids,
                            message=message.GameFinishedMessage(game=game_schema, result=verbose_result),
                        )
        except exceptions.NotAPlayer:
            pass
        except Exception as e:
            raise e


@router.websocket('/renju/ws')
async def renju(websocket: WebSocket, user: User = Depends(get_current_user)):
    await RenjuWSEndpoint().dispatch(websocket, user)
