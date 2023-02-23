from fastapi import APIRouter, Depends

from app.core.db.deps import AsyncSession, get_async_session
from app.models.user import User
from app.schemas.game import (
    GameModeInGameSchema,
    GameSchemaOut,
    GameRules,
    ModesAndRules,
)
from app.api.services.games import GameService
from app.auth.deps import get_current_user_dependency

router = APIRouter()
get_current_user = get_current_user_dependency(is_verified=True)


@router.get(
    '/modes',
    response_model=ModesAndRules,
    description='Получить список доступных режимов игры, чтобы создать игру',
)
async def read_game_modes(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
):
    all_modes = await GameService(db).get_modes()
    rules = await GameService(db).get_current_rules()
    return ModesAndRules(modes=all_modes, rules=rules)


@router.put('/modes', response_model=GameRules)
async def update_rules(
        *,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
        modes: list[GameModeInGameSchema],
):
    return await GameService(db).get_current_rules(modes)


@router.get(
    '/games',
    response_model=list[GameSchemaOut],
    description='Получить список игр, к которым можно присоединиться (как игрок или зритель)',
)
async def read_available_games(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
):
    available_games = await GameService(db).get_available_games()
    return available_games


@router.get('/games/mine')
async def read_my_finished_games(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
):
    # TODO: Вернуть все Game с state=finished, user in get_players(game) ---
    return {'hello': f'Hi, {user.name}', 'resp': f'You are not finished any game yet'}
