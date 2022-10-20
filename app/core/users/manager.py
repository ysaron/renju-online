import uuid
from typing import Any

import aioredis
from fastapi import Depends, Request
from fastapi_users import FastAPIUsers, BaseUserManager, UUIDIDMixin, InvalidPasswordException
from fastapi_users.authentication import BearerTransport, RedisStrategy, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase

from app.config import config
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.email import EmailSchema
from app.core.db.utils import get_user_db
from app.core.email.sending import send_email

bearer_transport = BearerTransport(tokenUrl='auth/login')

if config.REDIS_HOST_PASSWORD:
    REDIS_HOST = f':{config.REDIS_HOST_PASSWORD}@{config.REDIS_HOST_NAME}'
else:
    REDIS_HOST = config.REDIS_HOST_NAME
redis = aioredis.from_url(f'redis://{REDIS_HOST}:{config.REDIS_PORT}', decode_responses=True)


def get_redis_strategy() -> RedisStrategy:
    return RedisStrategy(redis, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name='redis',
    transport=bearer_transport,
    get_strategy=get_redis_strategy,
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = config.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = config.VERIFICATION_TOKEN_SECRET

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        # обычно здесь отправляем "welcome"-email
        print(f'User {user.id} ({user.email}) has registered.')

    async def on_after_update(self, user: User, update_dict: dict[str, Any], request: Request | None = None) -> None:
        # здесь можно обновить юзера на data analytics платформе
        print(f"User {user.id} has been updated with {update_dict}.")

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None) -> None:
        email = EmailSchema(
            subject='FA_BP_test',
            email=[user.email],
            body={
                'title': 'Changing password',
                'username': user.name,
                'token': token,
            },
            template='forgot_password_email.html',
        )
        await send_email(email)
        print(f'User {user.id} has forgot his password. Reset token: {token}')

    async def on_after_reset_password(self, user: User, request: Request | None = None) -> None:
        # отправление емейла юзеру, что его пароль был изменен, и если он думает что его хакнули - пусть примет меры
        print(f"User {user.id} has reset their password.")

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None) -> None:
        email = EmailSchema(
            subject='FA_BP_test',
            email=[user.email],
            body={
                'title': 'Email verification',
                'username': user.name,
                'token': token,
            },
            template='verification_email.html',
        )
        await send_email(email)
        print(f'Verification requested for user {user.id}. Verification token: {token}')

    async def on_after_verify(self, user: User, request: Request | None = None) -> None:
        # Тут можно обновить инфу на data analytics платформе или отправить уведомительный емейл
        print(f"User {user.id} has been verified")

    async def on_before_delete(self, user: User, request: Request | None = None) -> None:
        # проверим ресурсы юзера, мб их нужно пометить как неактивные или рекурсивно удалить
        print(f"User {user.id} is going to be deleted")

    async def on_after_delete(self, user: User, request: Request | None = None) -> None:
        # пошлем емейл админу о данном событии
        print(f"User {user.id} is successfully deleted")

    async def validate_password(self, password: str, user: UserCreate | User) -> None:
        if len(password) < 8:
            raise InvalidPasswordException(reason='Password should be at least 8 characters')
        if user.email in password or password in user.email:
            raise InvalidPasswordException(reason='Password is too similar to email')


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


fa_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)
