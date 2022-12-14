import uuid
from datetime import datetime
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


class Board(list[list[int]]):
    def __init__(self, iterable: list[list[int]]):
        self.__validate_init(iterable)
        super().__init__(iterable)

    @classmethod
    def default(cls, fill: int = 0, *, size: int) -> 'Board':
        array = [[fill for _ in range(size)] for _ in range(size)]
        return cls(array)

    @staticmethod
    def __validate_init(iterable: list[list[int]]) -> None:
        if not all(isinstance(obj, list) for obj in iterable):
            raise TypeError('Board must be 2D list.')
        if not all(len(obj) == len(iterable) for obj in iterable):
            raise ValueError('Board must be square.')


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
        return self.determine_rules(chosen_modes)

    async def create_game(self, creator: User, game_data: GameCreateSchema) -> Game:
        if await self.__check_user_active_games(creator):
            raise exceptions.UnfinishedGame()

        chosen_modes = await self.get_modes(mode_ids=[m.id for m in game_data.modes])
        rules = self.determine_rules(chosen_modes)

        game = Game()
        game.is_private = game_data.is_private
        game.time_limit = rules.time_limit
        game.board_size = rules.board_size
        game.classic_mode = rules.classic_mode
        game.with_myself = rules.with_myself
        if rules.three_players:
            game.num_players = 3

        game.board = Board.default(size=rules.board_size)

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
    def determine_rules(modes: list[GameMode]) -> GameRules:
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

    async def get_game(self, game_id: uuid.UUID) -> Game | None:
        stmt = select(Game).where(Game.id == game_id)
        game = await self.__db.scalars(stmt)
        return game.one_or_none()

    async def join_game(self, player: User, game_id: uuid.UUID) -> tuple[Game, PlayerRoleEnum, bool]:
        """
        Присоединение нового игрока

        :return: ORM объект игры, роль игрока, открывается ли игра повторно
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
    async def __get_player_role_enums(game: Game) -> tuple[PlayerRoleEnum, ...]:
        """ Список ролей (енумов) игроков для данной игры """
        player_enums = [PlayerRoleEnum.first, PlayerRoleEnum.second]
        if game.num_players == 3:
            player_enums.append(PlayerRoleEnum.third)
        return tuple(player_enums)

    async def __get_players(self, game: Game) -> list[PlayerRole]:
        """ Список юзеров, записанных в игру в качестве игрока """
        pr_enums = await self.__get_player_role_enums(game)
        return [player for player in game.players if player.role in pr_enums]

    @staticmethod
    async def __get_spectators(game: Game) -> list[PlayerRole]:
        """ Список юзеров, записанных в игру в качестве зрителя """
        pr_enums = (PlayerRoleEnum.spectator,)
        return [player for player in game.players if player.role in pr_enums]

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
        pr_enums = await self.__get_player_role_enums(game)
        for pr_enum in pr_enums:
            player = await self.__get_player_by_role(game, role=pr_enum)
            if player is None:
                return pr_enum

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

    async def __check_spectator_seats(self, game: Game) -> bool:
        """ Возвращает True, если у игры есть свободное место для зрителя """
        spectators = await self.__get_spectators(game)
        return len(spectators) < config.MAX_SPECTATORS_NUM

    async def __check_players_ready(self, game: Game) -> bool:
        """ Возвращает True если все игроки подтвердили готовность """
        players = await self.__get_players(game)
        return all(pr.ready for pr in players)

    async def set_player_ready(self, player: User, game_id: uuid.UUID) -> tuple[Game, str, PlayerRoleEnum]:
        """
        Отметка готовности игрока

        :return: ORM объект игры, имя игрока, роль игрока
        :raise NoGameFound: если игры с данным ID не существует
        :raise NotInGame: если данный юзер не записан в игру
        :raise UnsuitableGameState: если игра уже начата или завершена
        :raise NotAPlayer: если юзер - не игрок
        """
        if (game := await self.get_game(game_id)) is None:
            raise exceptions.NoGameFound()
        if not await self.__check_user_in_game(user=player, game=game):
            raise exceptions.NotInGame()
        if game.state != GameStateEnum.created:
            raise exceptions.UnsuitableGameState()
        if (role := await self.__get_role_by_player(game, player)) == PlayerRoleEnum.spectator:
            raise exceptions.NotAPlayer()
        pr = await self.__get_player_by_role(game, role)
        pr.ready = True
        name, role = pr.player.name, pr.role
        await self.__db.commit()
        await self.__db.refresh(game)
        return game, name, role

    async def get_role_ready_to_move(self, game: Game) -> PlayerRoleEnum | None:
        players = await self.__get_players(game)
        for pr in players:
            if pr.can_move:
                return pr.role

    async def get_role_next_to_move(self, game: Game) -> PlayerRoleEnum:
        pr_enums = await self.__get_player_role_enums(game)
        role_ready_to_move = await self.get_role_ready_to_move(game)
        if not role_ready_to_move:
            return pr_enums[0]
        try:
            return pr_enums[pr_enums.index(role_ready_to_move) + 1]
        except IndexError:
            return pr_enums[0]
        except ValueError:      # index() не нашел элемент
            raise

    async def switch_turn_order(self, game: Game) -> Game:
        role_next_to_move = await self.get_role_next_to_move(game)
        current_player = await self.__get_player_by_role(game, role=role_next_to_move)
        current_player.can_move = True
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    async def start_game(self, game: Game) -> Game:
        """ Определяет очередность ходов, запускает игру """
        game = await self.switch_turn_order(game)
        game.state = GameStateEnum.pending
        game.started_at = datetime.now()
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    async def attempt_to_start_game(self, game: Game) -> Game | None:
        if all([
            await self.__get_empty_seat(game) is None,      # свободных мест нет, все заняты
            await self.__check_players_ready(game),         # READY=True у всех игроков
        ]):
            return await self.start_game(game)
