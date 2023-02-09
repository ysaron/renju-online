import uuid
from datetime import datetime
from typing import Literal, NamedTuple
from dataclasses import dataclass, field

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.models.game import GameMode, Game, PlayerRole, PlayerResult, Move
from app.models.user import User
from app.schemas.game import (
    GameModeInGameSchema,
    GameCreateSchema,
    GameRules,
    MoveInputSchema,
)
from app.enums.game import PlayerRoleEnum, GameStateEnum, PlayerResultEnum, PlayerResultReasonEnum
from app.core import exceptions


class Coord(NamedTuple):
    x: int
    y: int


@dataclass
class Cell:
    value: int
    coord: Coord


@dataclass(frozen=True)
class GameMetaWrapper:
    """ Обертка для передачи вместе с ORM-объектом Game доп. данных """
    game: Game
    current_role: PlayerRoleEnum | None = None
    current_player_name: str | None = None
    reopen: bool = False
    delete: bool = False


@dataclass(frozen=True)
class MoveMetaWrapper:
    """  """
    move: Move
    game: Game
    winning_cells: list[Cell] = field(default_factory=list)


class RenjuBoard(list[list[Cell]]):

    @classmethod
    def default(cls, fill: int = 0, *, size: int) -> 'RenjuBoard':
        array = [[Cell(value=fill, coord=Coord(x, y)) for x in range(1, size + 1)] for y in range(1, size + 1)]
        return cls(array)

    @classmethod
    def from_string(cls, string: str) -> 'RenjuBoard':
        """
        :param string: Игровая доска в строковом виде (из БД)
        :raise ValueError: если строка не соотв. формату "ddd.ddd.ddd"
        """
        array = []
        for y, row in enumerate(string.split('.'), start=1):
            array_row = []
            for x, value in enumerate(row, start=1):
                cell = Cell(value=int(value), coord=Coord(x, y))
                array_row.append(cell)
            array.append(array_row)
        if not all(len(obj) == len(array) for obj in array):
            raise ValueError('Board must be square.')
        return cls(array)

    @property
    def as_string(self) -> str:
        return '.'.join(''.join(str(cell.value) for cell in row) for row in self)

    @property
    def as_array(self) -> list[list[int]]:
        return [[cell.value for cell in row] for row in self]

    @property
    def columns(self) -> list[list[Cell]]:
        return [list(col) for col in zip(*self)]

    @property
    def diagonals(self) -> list[list[Cell]]:
        primary_diagonals = []
        secondary_diagonals = []
        for offset in range(1 - len(self), len(self)):
            prim_diag = []
            sec_diag = []
            for i, row in enumerate(self):
                if -len(row) < offset - i <= 0:
                    prim_diag.append(row[offset - i - 1])
                if 0 <= i + offset < len(row):
                    sec_diag.append(row[i + offset])
            primary_diagonals.append(prim_diag)
            secondary_diagonals.append(sec_diag)
        return primary_diagonals + secondary_diagonals

    def move(self, new_cell: MoveInputSchema):
        print(f'{new_cell.value = }')
        print(f'cell: {new_cell.x} {new_cell.y}')
        if self[new_cell.y - 1][new_cell.x - 1].value:
            raise exceptions.CellOccupied()
        self[new_cell.y - 1][new_cell.x - 1].value = new_cell.value

    @staticmethod
    def __check_line(line: list[Cell], length: int = 5) -> list[Cell]:
        """
        Проверка, содержит ли линия ``length`` одинаковых значений подряд

        :return: список победных клеток
        """
        current_value = 0
        counter = 0
        winning_cells = []
        for cell in line:
            if cell.value == 0:
                winning_cells.clear()
                current_value = 0
                counter = 0
                continue
            winning_cells.append(cell)
            if cell.value == current_value:
                counter += 1
                if counter >= length:
                    return winning_cells
            else:
                counter = 1
            current_value = cell.value
        return []

    def check_victory(self) -> list[Cell]:
        """
        :return: список клеток-победителей либо пустой список, если условие победы не выполнено
        """
        for row in self:
            if winning_cells := self.__check_line(row):
                # return winning_cells[0].value, [cell.coord for cell in winning_cells]
                return winning_cells
        for column in self.columns:
            if winning_cells := self.__check_line(column):
                return winning_cells
        for diagonal in self.diagonals:
            if winning_cells := self.__check_line(diagonal):
                return winning_cells
        return []

    def check_free_space(self) -> bool:
        """
        :return: True, если на доске есть место для ходов
        """
        return True


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

    async def create_game(self, creator: User, game_data: GameCreateSchema) -> GameMetaWrapper:
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

        game.board = RenjuBoard.default(size=rules.board_size).as_string

        pr = PlayerRole(role=PlayerRoleEnum.first)
        pr.player = creator
        pr.result = PlayerResult()
        game.players.append(pr)

        for m in chosen_modes:
            game.modes.append(m)

        self.__db.add(game)
        await self.__db.commit()
        await self.__db.refresh(game)
        return GameMetaWrapper(game=game)

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
                return [pr.game for pr in user.games if pr.ready and pr.result.result is None]
            case 'finished':
                return [pr.game for pr in user.games if pr.game.state == GameStateEnum.finished]
            case _:
                return [pr.game for pr in user.games]

    async def get_game(self, game_id: uuid.UUID) -> Game | None:
        stmt = select(Game).where(Game.id == game_id)
        game = await self.__db.scalars(stmt)
        return game.one_or_none()

    async def join_game(self, player: User, game_id: uuid.UUID) -> GameMetaWrapper:
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
            pr = await self.__get_game_player_association(game, player)
            return GameMetaWrapper(game=game, current_role=pr.role, reopen=True)
        if (role := await self.__get_empty_seat(game)) is None:
            raise exceptions.NoEmptySeats()
        if await self.__check_user_active_games(player):
            raise exceptions.UnfinishedGame()
        game = await self.__write_player_to_game(player=player, game=game, role=role)
        return GameMetaWrapper(game=game, current_role=role)

    @staticmethod
    async def __get_player_role_enums(game: Game) -> tuple[PlayerRoleEnum, ...]:
        """ Список ролей (енумов) игроков для данной игры """
        player_enums = [PlayerRoleEnum.first, PlayerRoleEnum.second]
        if game.num_players == 3:
            player_enums.append(PlayerRoleEnum.third)
        return tuple(player_enums)

    async def __get_players(self, game: Game, only_active: bool = False) -> list[PlayerRole]:
        """
        Список юзеров, записанных в игру в качестве игрока

        :param game: ORM объект игры
        :param only_active: если True, вернутся только игроки, не завершившие игру
        :return: список ассоциаций game-player
        """
        pr_enums = await self.__get_player_role_enums(game)
        players = [player for player in game.players if player.role in pr_enums]
        if only_active:
            players = [player for player in players if player.result.result is None]
        return players

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
        pr = PlayerRole(role=role, player=player, result=PlayerResult())
        game.players.append(pr)
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    async def __check_user_active_games(self, user: User) -> bool:
        """ Возвращает True, если юзер имеет незаконченную игру """
        # Юзер не закончил игру, если ready уже нажато, но результат игры еще не записан
        active_games = await self.get_user_games(user, scope='active')
        return bool(active_games)

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
    async def __get_game_player_association(game: Game, player: User) -> PlayerRole | None:
        for pr in game.players:
            if pr.player.id == player.id:
                return pr

    async def __check_spectator_seats(self, game: Game) -> bool:
        """ Возвращает True, если у игры есть свободное место для зрителя """
        spectators = await self.__get_spectators(game)
        return len(spectators) < config.MAX_SPECTATORS_NUM

    async def __check_players_ready(self, game: Game) -> bool:
        """ Возвращает True если все игроки подтвердили готовность """
        players = await self.__get_players(game)
        return all(pr.ready for pr in players)

    async def set_player_ready(self, player: User, game_id: uuid.UUID) -> GameMetaWrapper:
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
        pr = await self.__get_game_player_association(game, player)
        if pr.role == PlayerRoleEnum.spectator:
            raise exceptions.NotAPlayer()
        pr.ready = True
        name, role = pr.player.name, pr.role
        await self.__db.commit()
        await self.__db.refresh(game)
        return GameMetaWrapper(game=game, current_player_name=name, current_role=role)

    async def get_role_ready_to_move(self, game: Game) -> PlayerRoleEnum | None:
        players = await self.__get_players(game)
        for pr in players:
            if pr.can_move:
                return pr.role

    async def get_role_next_to_move(self, game: Game, previous: PlayerRoleEnum) -> PlayerRoleEnum:
        pr_enums = await self.__get_player_role_enums(game)
        if not previous:
            return pr_enums[0]
        try:
            return pr_enums[pr_enums.index(previous) + 1]
        except IndexError:
            return pr_enums[0]
        except ValueError:  # index() не нашел элемент
            raise

    async def switch_turn_order(self, game: Game) -> Game:
        role_ready_to_move = await self.get_role_ready_to_move(game)
        role_next_to_move = await self.get_role_next_to_move(game, previous=role_ready_to_move)
        previous_player = await self.__get_player_by_role(game, role=role_ready_to_move)
        current_player = await self.__get_player_by_role(game, role=role_next_to_move)
        if previous_player:
            previous_player.can_move = False
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
            await self.__get_empty_seat(game) is None,  # свободных мест нет, все заняты
            await self.__check_players_ready(game),  # READY=True у всех игроков
        ]):
            return await self.start_game(game)

    async def move(self, player: User, cell: MoveInputSchema, game_id: uuid.UUID) -> MoveMetaWrapper:
        if (game := await self.get_game(game_id)) is None:
            raise exceptions.NoGameFound()
        if not await self.__check_user_in_game(user=player, game=game):
            raise exceptions.NotInGame()
        pr = await self.__get_game_player_association(game, player)
        pr_enums = await self.__get_player_role_enums(game)
        if pr.role not in pr_enums:
            raise exceptions.NotAPlayer()
        if not pr.can_move:
            # пришел клик от игрока, который по идее и не мог ходить. Просто игнорим, никаких сбщ в ответ.
            # allow_move=false у него и так проставилось там, раз еще не было. 2 раз не кликнет
            raise exceptions.FalseClick()
        # создаем Board из game.board
        board = RenjuBoard.from_string(game.board)
        # делаем board.move(move_obj)
        cell.value = int(pr.role.value)
        try:
            # print(f'BEFORE {board = }')
            board.move(cell)
            # print(f'AFTER {board = }')
        except IndexError as e:
            # может возникнуть в теории
            raise e
        except exceptions.CellOccupied:
            # если клетка занята - запрос надо игнорировать так же, как при not player.can_move
            raise exceptions.FalseClick()

        # если успешно (клетка не занята) - пишем Move в БД, пишем Baord в game.board
        move = Move()
        move.role = pr.role
        move.x = cell.x
        move.y = cell.y
        game.moves.append(move)

        game.board = board.as_string

        await self.__db.commit()
        await self.__db.refresh(game)
        await self.__db.refresh(move)
        # print(f'{game.board = }')

        # вызываем проверок в Board
        # от результата проверок зависит шо делаем и шо отправляем обратно
        if winning_cells := board.check_victory():
            # условие 5 в ряд выполнено
            pr_enum = PlayerRoleEnum(str(winning_cells[0].value))
            pr = await self.__get_player_by_role(game, pr_enum)
            game = await self.__set_players_result(players=[pr], game=game, result=PlayerResultEnum.win,
                                                   reason=PlayerResultReasonEnum.fair)
            return MoveMetaWrapper(
                move=move,
                game=await self.finish_game(game, reason=PlayerResultReasonEnum.fair),
                winning_cells=winning_cells,
            )
        if not board.check_free_space():
            # делать ходы больше некуда. Всем оставшимся игрокам ставим ничью
            active_players = await self.__get_players(game, only_active=True)
            game = await self.__set_players_result(players=active_players, game=game, result=PlayerResultEnum.draw,
                                                   reason=PlayerResultReasonEnum.full_board)
            return MoveMetaWrapper(move=move, game=await self.finish_game(game))
        # игра продолжается
        return MoveMetaWrapper(move=move, game=await self.switch_turn_order(game))

    async def leave(self, player: User, game_id: uuid.UUID) -> GameMetaWrapper:
        if (game := await self.get_game(game_id)) is None:
            raise exceptions.NoGameFound()
        if not await self.__check_user_in_game(user=player, game=game):
            raise exceptions.NotInGame()
        pr = await self.__get_game_player_association(game, player)
        pr_enums = await self.__get_player_role_enums(game)
        if pr.role not in pr_enums:
            raise exceptions.NotAPlayer()
        if pr.ready:
            return await self.__player_concede(pr, game)
        else:
            return await self.__player_leave(pr, game)

    async def __remove_player(self, pr: PlayerRole, game: Game) -> Game:
        await self.__db.delete(pr)
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    async def remove_game(self, game: Game) -> None:
        await self.__db.delete(game)
        await self.__db.commit()

    async def __player_leave(self, pr: PlayerRole, game: Game) -> GameMetaWrapper:
        game = await self.__remove_player(pr, game)
        if not await self.__get_players(game):
            return GameMetaWrapper(game=game, delete=True)
        return GameMetaWrapper(game=game)

    async def __player_concede(self, pr: PlayerRole, game: Game) -> GameMetaWrapper:
        players = await self.__get_players(game)
        if len(players) == 1:
            return GameMetaWrapper(game=game, delete=True)

        game = await self.__set_players_result(players=[pr], game=game, result=PlayerResultEnum.lose,
                                               reason=PlayerResultReasonEnum.concede)
        active_players = await self.__get_players(game, only_active=True)
        num_active_players = len(active_players)
        if num_active_players > 1:
            return GameMetaWrapper(game=game)
        if num_active_players == 1:
            game = await self.__set_players_result(players=active_players, game=game, result=PlayerResultEnum.win,
                                                   reason=PlayerResultReasonEnum.tech)
        return GameMetaWrapper(game=await self.finish_game(game))

    async def __set_players_result(
            self,
            players: list[PlayerRole],
            game: Game,
            result: PlayerResultEnum,
            reason: PlayerResultReasonEnum,
    ) -> Game:
        """
        :param players: список ORM-объектов игроков, которым проставляются результаты
        :param game: ORM-объект соответствующей игры
        :param result: проставляемый результат
        :param reason: причина проставляемого результата
        :return: обновленный ORM-объект соответствующей игры
        """
        if not players:
            return game
        for pr in players:
            pr.result.result = result
            pr.result.reason = reason
        await self.__db.commit()
        await self.__db.refresh(game)
        return game

    async def finish_game(self, game: Game, reason: PlayerResultReasonEnum = PlayerResultReasonEnum.tech) -> Game:
        """
        Завершает игру

        :param game: ORM-объект завершаемой игры
        :param reason: причина завершения игры
        :return: ORM-объект завершенной игры
        """
        # простановка поражения игрокам с еще не проставленным результатом
        active_players = await self.__get_players(game, only_active=True)
        game = await self.__set_players_result(players=active_players, game=game, result=PlayerResultEnum.lose,
                                               reason=reason)
        game.state = GameStateEnum.finished
        game.finished_at = datetime.now()
        await self.__db.commit()
        await self.__db.refresh(game)
        return game
