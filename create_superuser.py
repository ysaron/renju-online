import asyncio
import platform
from contextlib import asynccontextmanager

from app.auth.services import UserService
from app.core.db.deps import get_async_session
from app.core.exceptions import UserAlreadyExists
from app.schemas.user import UserCreateProgrammatically
from app.config import config

get_async_session_context = asynccontextmanager(get_async_session)


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


if __name__ == '__main__':
    if platform.system() == 'Windows':
        # во избежание "RuntimeError: Event loop is closed"
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(create_superuser())
