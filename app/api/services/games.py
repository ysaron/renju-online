
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import GameMode, Game, GameResult, PlayerRole, Move
from app.models.user import User
from app.schemas.game import GameModeInGameSchema, GameCreateSchema
from app.enums.game import PlayerRoleEnum, GameStateEnum


async def get_game_modes(db: AsyncSession, pk_list: list | None = None) -> list[GameMode]:
    stmt = select(GameMode)
    if pk_list is not None:
        stmt = stmt.where(GameMode.id.in_(pk_list))
    modes = await db.scalars(stmt)
    return modes.all()


async def create_game(db: AsyncSession, user: User, game_data: GameCreateSchema) -> Game:
    chosen_modes = await get_game_modes(db, pk_list=[m.id for m in game_data.modes])
    rules = await _define_game_rules(chosen_modes)

    game = Game()
    game.is_private = game_data.is_private
    game.time_limit = rules['time_limit']
    game.board_size = rules['board_size']
    game.classic_mode = rules['classic_mode']
    game.with_myself = rules['with_myself']

    pr = PlayerRole(role=PlayerRoleEnum.first)
    pr.player = user
    game.players.append(pr)

    for m in chosen_modes:
        game.modes.append(m)

    db.add(game)

    await db.commit()
    await db.refresh(game)
    return game


async def _define_game_rules(modes: list[GameMode]):
    rules = {
        'time_limit': None,
        'board_size': 15,
        'classic_mode': False,
        'with_myself': False,
    }
    for mode in modes:
        if mode.time_limit == 0:
            rules['time_limit'] = None
        elif mode.time_limit is not None:
            rules['time_limit'] = mode.time_limit

        if mode.board_size is not None:
            rules['board_size'] = mode.board_size

        if mode.classic_mode is not None:
            rules['classic_mode'] = mode.classic_mode

        if mode.with_myself is not None:
            rules['with_myself'] = mode.with_myself

    return rules


async def get_public_games(db: AsyncSession) -> list[Game]:
    stmt = select(Game).where(and_(
        Game.state == GameStateEnum.created,
        ~Game.with_myself,
        ~Game.is_private,
    ))
    public_games = await db.scalars(stmt)
    return public_games.all()


