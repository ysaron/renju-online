import uuid
from datetime import datetime
from typing import Type, Any

from pydantic import BaseModel, Field

from .user import UserRead
from app.enums.game import PlayerRoleEnum, GameStateEnum, PlayerResultEnum, PlayerResultReasonEnum


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


class ResultSchema(BaseModel):
    result: PlayerResultEnum | None = None
    reason: PlayerResultReasonEnum | None = None

    class Config:
        orm_mode = True


class PlayerSchema(BaseModel):
    player: UserRead
    ready: bool = False
    can_move: bool = False
    role: PlayerRoleEnum | None = None
    result: ResultSchema

    class Config:
        orm_mode = True


class MoveInputSchema(BaseModel):
    value: int = Field(0, ge=0, le=3)
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)

    class Config:
        orm_mode = True


class MoveSchema(MoveInputSchema):
    id: int
    role: PlayerRoleEnum


class GameJoinSchema(GameBaseSchema):
    id: uuid.UUID


class GameCreateSchema(GameBaseSchema):
    is_private: bool = Field(False, description='Если True - доступна только по ссылке')
    modes: list[GameModeInGameSchema]


class GameSchema(GameCreateSchema):
    id: uuid.UUID
    state: GameStateEnum
    players: list[PlayerSchema] = Field(..., max_items=3, description='Игроки (до 3)')
    num_players: int = Field(2, ge=2, le=3, description='Кол-во игроков')
    time_limit: int | None = Field(None, ge=0, le=1200, description='Время, отведенное игрокам на ходы (с)')
    board_size: int = Field(..., gt=10, le=40, description='Длина стороны квадратного поля (в клетках)')
    classic_mode: bool = Field(..., description='Включить классические правила рэндзю')
    with_myself: bool = Field(..., description='Игра с самим собой')
    board: str | list[list[int]]
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    moves: list[MoveSchema]

    def get_player_by_role(self, role: PlayerRoleEnum) -> PlayerSchema | None:
        for player in self.players:
            if player.role == role:
                return PlayerSchema(**player.dict())

    def get_spectators(self) -> list[PlayerSchema]:
        return [PlayerSchema(**player.dict()) for player in self.players if player.role == PlayerRoleEnum.spectator]


class GameSchemaOut(GameSchema):
    """ Схема для получения более удобного JSON для клиента """

    player_1: PlayerSchema | None = None
    player_2: PlayerSchema | None = None
    player_3: PlayerSchema | None = None
    spectators: list[PlayerSchema] = Field([], max_items=10)

    @classmethod
    def from_orm(cls: Type['GameSchema'], obj: Any) -> 'GameSchemaOut':
        instance = super().from_orm(obj)
        schema = GameSchemaOut(**instance.dict())
        schema.player_1 = instance.get_player_by_role(PlayerRoleEnum.first)
        schema.player_2 = instance.get_player_by_role(PlayerRoleEnum.second)
        schema.player_3 = instance.get_player_by_role(PlayerRoleEnum.third)
        schema.spectators = instance.get_spectators()
        schema.players = None
        schema.board = [[int(cell) for cell in row] for row in schema.board.split('.')]     # дубл. Board.from_string()
        return schema

    def current_player(self) -> PlayerSchema | None:
        for player in [self.player_1, self.player_2, self.player_3]:
            if not player:
                continue
            if player.can_move:
                return player

    def winner(self) -> PlayerSchema | None:
        """ Возвращает схему победителя, если он существует """
        for player in [self.player_1, self.player_2, self.player_3]:
            if not player:
                continue
            if player.result.result == PlayerResultEnum.win:
                return player

    def draw_players(self) -> list[PlayerSchema]:
        """ Список игроков, которым зачтена ничья """
        players = []
        for player in [self.player_1, self.player_2, self.player_3]:
            if not player:
                continue
            if player.result.result == PlayerResultEnum.draw:
                players.append(player)
        return players

    def verbose_result(self) -> str:
        """ Результат игры для отображения игрокам по ее окончании """
        if winner := self.winner():
            return f'{winner.player.name} won! ({winner.result.reason.value})'
        if draw_players := self.draw_players():
            return f'Draw ({draw_players[0].result.reason.value})'
        return ''


class GameFullSchema(GameSchema):
    started_at: datetime | None = None
    finished_at: datetime | None = None
    moves: list[MoveSchema]


class ModesAndRules(BaseModel):
    modes: list[GameModeSchema]
    rules: GameRules
