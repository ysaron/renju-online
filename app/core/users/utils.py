from contextlib import asynccontextmanager

from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr

from app.core.db.utils import get_async_session, get_user_db
from app.schemas.user import UserCreate
from .manager import get_user_manager

get_async_session_context = asynccontextmanager(get_async_session)
get_user_db_context = asynccontextmanager(get_user_db)
get_user_manager_context = asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, name: str, is_superuser: bool = False, is_verified: bool = False):
    """
    Создает юзера.

    Поскольку скрипт находится вне Dependency Injection системы,
    зависимости-генераторы трансформируем в контекстные менеджеры и
    создаем их экземпляры вручную.

    https://fastapi-users.github.io/fastapi-users/10.2/cookbook/create-user-programmatically/#1-define-dependencies-as-context-managers
    """
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user_data = UserCreate(
                        email=EmailStr(email),
                        password=password,
                        name=name,
                        is_superuser=is_superuser,
                        is_active=True,
                        is_verified=is_verified,
                    )
                    user = await user_manager.create(user_data)
                    print(f'User {user.email} ({user.name}) created. Admin: {user.is_superuser}')
    except UserAlreadyExists:
        print(f'User {email} ({name}) already exists')
