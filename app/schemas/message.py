from pydantic import BaseModel, Field

from .game import GameSchemaOut
from app.enums.game import PlayerRoleEnum


class BaseMessageSchema(BaseModel):
    action: str


class OpenGameMessage(BaseMessageSchema):
    action: str = 'open_game'
    game: GameSchemaOut
    my_role: PlayerRoleEnum


class GameAddedMessage(BaseMessageSchema):
    action: str = 'game_added'
    game: GameSchemaOut


class PlayerJoinedMessage(BaseMessageSchema):
    action: str = 'player_joined'
    game: GameSchemaOut
    player_name: str
    player_role: PlayerRoleEnum


class PlayerJoinedListMessage(PlayerJoinedMessage):
    action: str = 'player_joined_list'


class SpectatorJoinedMessage(BaseMessageSchema):
    action: str = 'spectator_joined'
    game: GameSchemaOut


class PlayerReadyMessage(BaseMessageSchema):
    action: str = 'ready'
    game: GameSchemaOut
    player_name: str
    player_role: PlayerRoleEnum


class GameStartedMessage(BaseMessageSchema):
    action: str = 'game_started'
    game: GameSchemaOut


class GameStartedListMessage(BaseMessageSchema):
    action: str = 'game_started_list'
    game: GameSchemaOut


class UnblockBoardMessage(BaseMessageSchema):
    action: str = 'unblock_board'
    game: GameSchemaOut


class ErrorMessage(BaseMessageSchema):
    action: str = 'error'
    detail: str
    scope: str = 'global'
