from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, declared_attr

from app.config import config

DB_URL = f'postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@db:' \
         f'{config.POSTGRES_PORT}/{config.POSTGRES_DB}'
engine = create_async_engine(DB_URL, future=True, echo=True)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=Base)
