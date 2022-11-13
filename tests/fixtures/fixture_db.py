import pytest
import pytest_asyncio
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.core.db.base import Base
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
