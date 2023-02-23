import uuid

from unittest.mock import patch
import asynctest
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import generate_jwt, decode_jwt
from app.config import config
from app.models.user import User
from app.schemas.user import UserCreate
from app.core import exceptions
from app.auth.services import UserService


class TestUserService:

    @staticmethod
    def get_verification_token(user_id: uuid.UUID) -> str:
        return generate_jwt(
            data={'user_id': str(user_id)},
            secret=config.VERIFICATION_TOKEN_SECRET,
            lifetime_sec=config.ACCESS_TOKEN_EXPIRE_SECONDS,
        )

    @pytest.mark.anyio
    async def test_register_bad_password(self, async_session: AsyncSession, user_data):
        with pytest.raises(exceptions.PasswordTooShort):
            body = user_data['register']['bad']['short_password']
            await UserService(async_session).create_user(UserCreate(**body))

        with pytest.raises(exceptions.PasswordInsecure):
            body = user_data['register']['bad']['simple_password']
            await UserService(async_session).create_user(UserCreate(**body))

    @pytest.mark.anyio
    async def test_registration_full(self, async_session: AsyncSession, user_data):
        body = user_data['register']['good']
        await UserService(async_session).create_user(UserCreate(**body))

        # проверка, что пользователь был создан и создан корретно
        stmt = select(User).where(User.email == body['email'])
        result = await async_session.scalars(stmt)
        user = result.first()
        assert user.is_active
        assert not user.is_verified, 'Пользователь создался сразу же верифицированным'
        assert not user.is_superuser, 'Пользователь зарегистрировался как админ'
        assert user.name == body['name']

        # имитация отправки токена по email
        token = self.get_verification_token(user.id)
        with patch('app.auth.services.generate_jwt') as jwt_mock, \
                asynctest.patch('app.auth.services.send_email') as email_mock:
            jwt_mock.return_value = token
            await UserService(async_session).send_verify_token(user.email)
            jwt_mock.assert_called_once()
            email_mock.assert_called_once()

        # проверка, что пользователь был верифицирован
        await UserService(async_session).verify_user(token)
        await async_session.refresh(user)
        assert user.is_verified, 'Юзер не был верифицирован'

        # проверка, что нельзя зарегистрироваться с данными существующего пользователя
        with pytest.raises(exceptions.UserAlreadyExists):
            await UserService(async_session).create_user(UserCreate(**body))

    @pytest.mark.anyio
    async def test_login(self, async_session: AsyncSession, user_data):
        # создание пользователя
        create_body = user_data['register']['good']
        user = await UserService(async_session).create_user(UserCreate(**create_body))

        # попытка залогиниться, не будучи верифицированным
        with pytest.raises(exceptions.UserNotVerified):
            await UserService(async_session).login(**user_data['login']['good'])

        # верификация
        token = self.get_verification_token(user.id)
        await UserService(async_session).verify_user(token)

        # попытка залогиниться, не будучи зарегистрированным
        with pytest.raises(exceptions.UserNotExists):
            await UserService(async_session).login(**user_data['login']['wrong_email'])

        # попытка залогиниться неверным паролем
        with pytest.raises(exceptions.BadCredentials):
            await UserService(async_session).login(**user_data['login']['bad_credentials'])

        token_response = await UserService(async_session).login(**user_data['login']['good'])
        # проверка корректности токена
        payload = decode_jwt(token_response.access_token, secret=config.JWT_SECRET_KEY)
        await async_session.refresh(user)
        assert payload.get('email') == user.email, 'Юзер не может авторизоваться'

    @pytest.mark.anyio
    async def test_reset_password(self, async_session: AsyncSession, user_data):
        # создание и верификация пользователя
        create_body = user_data['register']['good']
        user = await UserService(async_session).create_user(UserCreate(**create_body))
        token = self.get_verification_token(user.id)
        await UserService(async_session).verify_user(token)
        await async_session.refresh(user)

        # имитация отправки токена для сброса пароля
        reset_password_token = generate_jwt(
            data={'user_id': str(user.id)},
            secret=config.RESET_PASSWORD_TOKEN_SECRET,
            lifetime_sec=config.ACCESS_TOKEN_EXPIRE_SECONDS,
        )
        with patch('app.auth.services.generate_jwt') as jwt_mock, \
                asynctest.patch('app.auth.services.send_email') as email_mock:
            jwt_mock.return_value = reset_password_token
            await UserService(async_session).forgot_password(user.email)
            jwt_mock.assert_called_once()
            email_mock.assert_called_once()

        # сброс пароля
        new_password = 'some_new_password'
        await UserService(async_session).reset_password(reset_password_token, plain_password=new_password)
        await async_session.refresh(user)

        # попытка залогиниться новым паролем
        await UserService(async_session).login(email=create_body['email'], password=new_password)
