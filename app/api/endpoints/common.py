from fastapi import APIRouter, Depends, Query, Body

from app.core.db.deps import AsyncSession, get_async_session
from app.models.user import User
from app.schemas.game import (
    GameModeSchema,
    GameModeInGameSchema,
    GameJoinSchema,
    GameCreateSchema,
    GameSchema,
    GameAvailableListSchema,
    GameRules,
    ModesAndRules,
)
from app.api.services import games as game_services
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
    all_modes = await game_services.get_game_modes(db)
    rules = await game_services.get_current_rules(db)
    return ModesAndRules(modes=all_modes, rules=rules)


@router.put('/modes', response_model=GameRules)
async def update_rules(
        *,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
        modes: list[GameModeInGameSchema],
):
    return await game_services.get_current_rules(db, modes)


@router.post('/games/create', response_model=GameSchema, description='Создание новой игры')
async def create_new_game(
        *,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
        game: GameCreateSchema,
):
    game = await game_services.create_game(db, user=user, game_data=game)
    return game


@router.get(
    '/games',
    response_model=list[GameAvailableListSchema],
    description='Получить список игр, к которым можно присоединиться (как игрок или зритель)',
)
async def read_available_games(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
):
    available_games = await game_services.get_available_games(db)
    return available_games


@router.get('/games/mine')
async def read_my_finished_games(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),
):
    # --- Возвращаем все Game с state=finished, user in get_players(game)
    # --- response_model=list[GameFinishedListSchema] ---
    return {'hello': f'Hi, {user.name}', 'resp': f'You are not finished any game yet'}
