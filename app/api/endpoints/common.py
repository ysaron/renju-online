from uuid import UUID

from fastapi import APIRouter, Depends, Query, Body

from app.core.users.manager import fa_users
from app.core.db.utils import AsyncSession, get_async_session
from app.models.user import User
from app.schemas.game import (
    GameModeSchema,
    GameModeInGameSchema,
    GameModeCreateSchema,
    GameJoinSchema,
)

router = APIRouter()
current_user = fa_users.current_user(active=True, verified=True)


@router.get('/games/create')
async def read_game_modes(
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
):
    # --- Получаем список всех GameMode и возвращаем ---
    # --- response_model=list[GameModeSchema] с exclude_unset ---
    return {'hello': f'Hi, {user.name}', 'resp': 'No game modes exist yet'}


@router.post('/games/create')
async def create_new_game(
        *,
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
        modes: list[GameModeInGameSchema],
):
    # --- Создаем новый экземпляр Game и возвращаем ---
    # --- response_model=GameSchema ---
    return {'hello': f'Hi, {user.name}', 'resp': 'Game is not created yet'}


@router.get('/games')
async def read_public_games(
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
):
    # --- Возвращаем все Game с state=created, with_myself=False, is_private=False
    # --- response_model=list[GameAvailableListSchema] ---
    return {'hello': f'Hi, {user.name}', 'resp': 'No available games'}


@router.get('/games/mine')
async def read_my_finished_games(
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
):
    # --- Возвращаем все Game с state=finished, user in get_players(game)
    # --- response_model=list[GameFinishedListSchema] ---
    return {'hello': f'Hi, {user.name}', 'resp': f'You are not finished any game yet'}


@router.patch('/games/{game_id}')
async def join_game(
        *,
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
        game_id: UUID,
):
    # --- Добавляем текущего юзера к Game по ID ---
    return {'hello': f'Hi, {user.name}', 'resp': 'No game to join'}


@router.post('/games/{game_id}/surrender')
async def surrender(
        *,
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
        game_id: UUID,
):
    # --- текущий юзер проигрывает. Запускается процесс завершения игры ---
    return {'hello': f'Hi, {user.name}', 'resp': f'Cannot lose in game {game_id}'}


@router.get('/games/{game_id}/open')
async def open_game(
        *,
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_async_session),
        game_id: UUID,
):
    # --- if user in get_players(game) AND game.state in [created, started]: ---
    # --- открываем окно игры, дальше - вебсокеты ---
    return {'hello': f'Hi, {user.name}', 'resp': f'Try to open game {game_id}'}
