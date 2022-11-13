from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routes import routes
from app.api.services.game_modes import bulk_create_game_modes
from app.auth.services import UserService
from app.core.db.deps import get_async_session
from app.core.exceptions import UserAlreadyExists
from app.schemas.user import UserCreateProgrammatically
from app.config import config

get_async_session_context = asynccontextmanager(get_async_session)

app = FastAPI()

app.include_router(routes)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS.split(),
    allow_credentials=True,     # разрешает cookies
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def create_superuser():
    user_schema = UserCreateProgrammatically(
        name=config.ADMIN_USERNAME,
        email=config.ADMIN_EMAIL,
        password=config.ADMIN_PASSWORD,
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    async with get_async_session_context() as db:
        try:
            await UserService(db).create_user(user_schema)
            print(f'User {user_schema.name} created.')
        except UserAlreadyExists:
            print(f'User {user_schema.name} already exists.')


@app.on_event('startup')
async def create_game_modes():
    await bulk_create_game_modes()


if __name__ == '__main__':
    uvicorn.run('main:app', host=config.APP_HOST, port=config.APP_PORT, reload=True)
