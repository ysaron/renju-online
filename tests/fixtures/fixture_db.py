import json

import pytest
import pytest_asyncio
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.core.db.base import Base
from app.api.services.game_modes import bulk_create_game_modes
from app.api.services.games import GameService
from app.auth.services import UserService
from app.schemas.game import GameModeInGameSchema
from app.schemas.user import UserCreateProgrammatically
from main import app

DB_URL = f'postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@db:' \
         f'{config.POSTGRES_PORT}/{config.POSTGRES_DB}_tests'
engine = create_async_engine(DB_URL, future=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        app=app,
        base_url=f'{config.APP_SCHEMA}://{config.REMOTE_HOST}',
    ) as client:
        yield client


@pytest_asyncio.fixture(scope='function')
async def async_session():
    async with async_session_maker() as db:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield db

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope='function')
def user_data() -> dict:
    data_file = config.BASE_DIR / 'tests' / 'fixtures' / 'data' / 'user_data.json'
    with open(data_file, 'r') as file:
        data = json.load(file)

    return data


@pytest_asyncio.fixture(scope='function')
async def modes(async_session) -> list[GameModeInGameSchema]:
    await bulk_create_game_modes(async_session)
    modes_orm = await GameService(async_session).get_modes()
    return [GameModeInGameSchema(name=mode.name, id=mode.id) for mode in modes_orm if mode.is_active]


@pytest_asyncio.fixture(scope='function')
async def modes_no(modes: list[GameModeInGameSchema]):
    return []


@pytest_asyncio.fixture(scope='function')
async def modes_public(modes: list[GameModeInGameSchema]):
    return [mode for mode in modes if mode.name == 'Trinity']


@pytest_asyncio.fixture(scope='function')
async def modes_private(modes: list[GameModeInGameSchema]):
    return [mode for mode in modes if mode.name in ['Trinity', 'Standalone']]


@pytest_asyncio.fixture(scope='function')
async def test_user(async_session):
    user_schema = UserCreateProgrammatically(
        name=config.TEST_USER_USERNAME,
        email=config.TEST_USER_EMAIL,
        password=config.TEST_USER_PASSWORD,
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    return await UserService(async_session).create_user(user_schema)
