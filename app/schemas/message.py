from pydantic import BaseModel, Field

from .game import GameSchemaOut
from app.enums.game import PlayerRoleEnum


class BaseMessageSchema(BaseModel):
    action: str


class GameCreatedMessage(BaseMessageSchema):
    action: str = 'game_created'
    game: GameSchemaOut
    my_role: PlayerRoleEnum | None = None


class GameAddedMessage(BaseMessageSchema):
    action: str = 'game_added'
    game: GameSchemaOut


class ErrorMessage(BaseMessageSchema):
    action: str = 'error'
    detail: str
    scope: str = 'global'
