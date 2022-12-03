import uuid
from typing import Literal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.models.game import GameMode, Game, PlayerRole
from app.models.user import User
from app.schemas.game import (
    GameModeInGameSchema,
    GameCreateSchema,
    GameRules,
)
from app.enums.game import PlayerRoleEnum, GameStateEnum
from app.core import exceptions


class GameService:

    def __init__(self, db_session: AsyncSession):
        self.__db = db_session

    async def get_modes(self, mode_ids: list[int] | None = None) -> list[GameMode]:
        stmt = select(GameMode)
        if mode_ids is not None:
            stmt = stmt.where(GameMode.id.in_(mode_ids))
        modes = await self.__db.scalars(stmt)
        return modes.all()

    async def get_current_rules(self, modes: list[GameModeInGameSchema] | None = None) -> GameRules:
        if not modes:
            return GameRules()
        chosen_modes = await self.get_modes(mode_ids=[m.id for m in modes])
        return self.define_rules(chosen_modes)

    async def create_game(self, creator: User, game_data: GameCreateSchema) -> Game:
        if await self.__check_user_active_games(creator):
            raise exceptions.UnfinishedGame()

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

    @staticmethod
    async def get_user_games(
            user: User,
            scope: Literal['nonstarted', 'active', 'finished', 'all'] = 'all',
    ) -> list[Game]:
        match scope:
            case 'nonstarted':
                return [pr.game for pr in user.games if pr.game.state == GameStateEnum.created]
            case 'active':
                return [pr.game for pr in user.games if pr.ready and pr.result is not None]
            case 'finished':
                return [pr.game for pr in user.games if pr.game.state == GameStateEnum.finished]
            case _:
                return [pr.game for pr in user.games]

    async def get_game(self, game_id: uuid.UUID) -> Game:
        stmt = select(Game).where(Game.id == game_id)
        game = await self.__db.scalars(stmt)
        return game.one_or_none()

    async def join_game(self, player: User, game_id: uuid.UUID) -> tuple[Game, PlayerRoleEnum, bool]:
        """
        Присоединение нового игрока

        :return: объект игры; роль игрока в ней; True, если игрок уже был записан и игра будет переоткрыта
        :raise NoGameFound: если игры с данным ID не существует
        :raise NoEmptySeats: если все места для игроков заняты
        :raise UnfinishedGame: если юзер все еще участвует как игрок в другой игре
        """
        if (game := await self.get_game(game_id)) is None:
            raise exceptions.NoGameFound()
        if await self.__check_user_in_game(user=player, game=game):
            role = await self.__get_role_by_player(game, player)
            return game, role, True
        if (role := await self.__get_empty_seat(game)) is None:
            raise exceptions.NoEmptySeats()
        if await self.__check_user_active_games(player):
            raise exceptions.UnfinishedGame()
        game = await self.__write_player_to_game(player=player, game=game, role=role)
        return game, role, False

    @staticmethod
    async def __check_user_in_game(user: User, game: Game) -> bool:
        """ Возвращает True, если юзер записан в игру как игрок или зритель """
        return any([pr.player.id == user.id for pr in game.players])

    async def __write_player_to_game(self, player: User, game: Game, role: PlayerRoleEnum) -> Game:
        """ Записывает юзера в игру как игрока """
        pr = PlayerRole(role=role, player=player)
        game.players.append(pr)
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    async def __check_user_active_games(self, user: User) -> bool:
        """ Возвращает True, если юзер имеет незаконченную игру """
        # Юзер не закончил игру, если ready уже нажато, но результат игры еще не записан
        return bool(await self.get_user_games(user, scope='active'))

    async def __get_empty_seat(self, game: Game) -> PlayerRoleEnum | None:
        """
        Определяет роль (номер) присоединяющегося игрока. Если занято место '1' - возвращается '2'.
        Если занято '2' и игра для троих игроков - возвращается '3'.

        :return: роль, в которой игрок будет прикреплен к игре; None, если свободных мест нет
        """
        player_enums = [PlayerRoleEnum.first, PlayerRoleEnum.second]
        if game.num_players == 3:
            player_enums.append(PlayerRoleEnum.third)
        for pl_enum in player_enums:
            player = await self.__get_player_by_role(game, role=pl_enum)
            if player is None:
                return pl_enum

    @staticmethod
    async def __get_player_by_role(game: Game, role: PlayerRoleEnum) -> PlayerRole | None:
        for pr in game.players:
            if pr.role == role:
                return pr

    @staticmethod
    async def __get_role_by_player(game: Game, player: User) -> PlayerRoleEnum | None:
        for pr in game.players:
            if pr.player.id == player.id:
                return pr.role

    @staticmethod
    def __check_spectator_seats(game: Game) -> bool:
        """ Возвращает True, если у игры есть свободное место для зрителя """
        spectator_enums = [PlayerRoleEnum.spectator]
        spectators = [player for player in game.players if player.role in spectator_enums]
        return len(spectators) < config.MAX_SPECTATORS_NUM
