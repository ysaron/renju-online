import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from .user import UserSchema
from app.enums.game import PlayerRoleEnum, GameStateEnum, GameResultEnum, GameResultCauseEnum


class GameModeBaseSchema(BaseModel):
    name: str = Field(..., max_length=40, description='Название режима игры')

    class Config:
        orm_mode = True


class GameBaseSchema(BaseModel):

    class Config:
        orm_mode = True


class GameRules(BaseModel):
    time_limit: int | None = Field(None, ge=0, le=1200, description='Время, отведенное игрокам на ходы (с)')
    board_size: int | None = Field(15, gt=10, le=40, description='Длина стороны квадратного поля (в клетках)')
    classic_mode: bool | None = Field(False, description='Включить классические правила рэндзю')
    with_myself: bool | None = Field(False, description='Игра с самим собой')
    three_players: bool | None = Field(False, description='Три игрока (каждый против каждого)')


class GameModeSchema(GameModeBaseSchema):
    id: int

    time_limit: int | None = Field(None, ge=0, le=1200, description='Время, отведенное игрокам на ходы (с)')
    board_size: int | None = Field(None, gt=10, le=40, description='Длина стороны квадратного поля (в клетках)')
    classic_mode: bool | None = Field(None, description='Включить классические правила рэндзю')
    with_myself: bool | None = Field(None, description='Игра с самим собой')
    three_players: bool | None = Field(None, description='Три игрока (каждый против каждого)')
    is_active: bool = Field(False, description='Доступен ли мод для игры')


class GameModeInGameSchema(GameModeBaseSchema):
    id: int


class PlayerRoleSchema(BaseModel):
    player: UserSchema
    role: PlayerRoleEnum
    ready: bool = False

    class Config:
        orm_mode = True


class ResultSchema(BaseModel):
    result: GameResultEnum
    cause: GameResultCauseEnum
    winner: UserSchema

    class Config:
        orm_mode = True


class MoveSchema(BaseModel):
    id: int
    player: UserSchema
    x_coord: int = Field(..., ge=0)
    y_coord: int = Field(..., ge=0)

    class Config:
        orm_mode = True


class GameJoinSchema(GameBaseSchema):
    id: uuid.UUID


class GameCreateSchema(GameBaseSchema):
    is_private: bool = Field(False, description='Если True - доступна только по ссылке')
    modes: list[GameModeInGameSchema]


class GameSchema(GameCreateSchema):
    id: uuid.UUID
    state: GameStateEnum
    players: list[PlayerRoleSchema] = Field(..., max_items=3, description='Игроки (до 3)')
    num_players: int = Field(2, ge=2, le=3, description='Кол-во игроков')
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: ResultSchema | None = None
    moves: list[MoveSchema]
    time_limit: int | None = Field(None, ge=0, le=1200, description='Время, отведенное игрокам на ходы (с)')
    board_size: int = Field(..., gt=10, le=40, description='Длина стороны квадратного поля (в клетках)')
    classic_mode: bool = Field(..., description='Включить классические правила рэндзю')
    with_myself: bool = Field(..., description='Игра с самим собой')


class GameAvailableListSchema(GameBaseSchema):
    id: uuid.UUID
    state: GameStateEnum
    players: list[PlayerRoleSchema] = Field(..., max_items=3, description='Игроки (до 3)')
    num_players: int = Field(2, ge=2, le=3, description='Кол-во игроков')
    created_at: datetime
    time_limit: int | None = Field(None, ge=0, le=1200, description='Время, отведенное игрокам на ходы (с)')
    board_size: int = Field(..., gt=10, le=40, description='Длина стороны квадратного поля (в клетках)')
    classic_mode: bool = Field(..., description='Включить классические правила рэндзю')
    with_myself: bool = Field(..., description='Игра с самим собой')


class GameFinishedListSchema(GameAvailableListSchema):
    started_at: datetime
    finished_at: datetime
    result: ResultSchema


class ModesAndRules(BaseModel):
    modes: list[GameModeSchema]
    rules: GameRules
