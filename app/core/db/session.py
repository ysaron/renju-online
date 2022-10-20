from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import config

DB_URL = f'postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@db:' \
         f'{config.POSTGRES_PORT}/{config.POSTGRES_DB}'
engine = create_async_engine(DB_URL, future=True)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
