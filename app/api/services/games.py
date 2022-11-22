
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import GameMode, Game, PlayerRole
from app.models.user import User
from app.schemas.game import (
    GameModeInGameSchema,
    GameCreateSchema,
    GameRules,
)
from app.enums.game import PlayerRoleEnum, GameStateEnum


class GameService:

    def __init__(self, db_session: AsyncSession):
        self.__db = db_session

    async def get_modes(self, mode_ids: list[int] | None = None) -> list[GameMode]:
        stmt = select(GameMode)
        if mode_ids:
            stmt = stmt.where(GameMode.id.in_(mode_ids))
        modes = await self.__db.scalars(stmt)
        return modes.all()

    async def get_current_rules(self, modes: list[GameModeInGameSchema] | None = None) -> GameRules:
        if not modes:
            return GameRules()
        chosen_modes = await self.get_modes(mode_ids=[m.id for m in modes])
        return self.define_rules(chosen_modes)

    async def create_game(self, creator: User, game_data: GameCreateSchema) -> Game:
        chosen_modes = await self.get_modes(mode_ids=[m.id for m in game_data.modes])
        rules = self.define_rules(chosen_modes)

        game = Game()
        game.is_private = game_data.is_private
        game.time_limit = rules.time_limit
        game.board_size = rules.board_size
        game.classic_mode = rules.classic_mode
        game.with_myself = rules.with_myself
        if rules.three_players:
            game.num_players = 3

        pr = PlayerRole(role=PlayerRoleEnum.first)
        pr.player = creator
        game.players.append(pr)

        for m in chosen_modes:
            game.modes.append(m)

        self.__db.add(game)
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    @staticmethod
    def define_rules(modes: list[GameMode]) -> GameRules:
        """ Определяет правила игры на основе комбинации модификаций """
        rules = GameRules()
        if not modes:
            return rules
        for mode in modes:
            if mode.time_limit == 0:
                rules.time_limit = None
            elif mode.time_limit is not None:
                rules.time_limit = mode.time_limit

            if mode.board_size is not None:
                rules.board_size = mode.board_size

            if mode.classic_mode is not None:
                rules.classic_mode = mode.classic_mode

            if mode.with_myself is not None:
                rules.with_myself = mode.with_myself

            if mode.three_players is not None:
                rules.three_players = mode.three_players

        return rules

    async def get_available_games(self) -> list[Game]:
        stmt = select(Game).where(and_(
            Game.state.in_([GameStateEnum.created, GameStateEnum.pending]),
            ~Game.with_myself,
            ~Game.is_private,
        ))
        available_games = await self.__db.scalars(stmt)
        return available_games.all()
