from datetime import datetime

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.db.deps import AsyncSession, get_async_session
from app.config import config
from .utils import decode_jwt
from .services import UserService


class OAuth2PasswordBearerWS(OAuth2PasswordBearer):
    """ Предотвращает вызов зависимости ``oauth2_scheme``, если подключение по вебсокету """
    async def __call__(self, request: Request = None):
        if not request:
            return None
        return await super().__call__(request)


oauth2_scheme = OAuth2PasswordBearerWS(tokenUrl='auth/login', scheme_name='JWT')


def get_current_user_dependency(
        is_verified: bool = False,
        is_superuser: bool = False,
        websocket_mode: bool = False,
):
    """
    Сборщик FastAPI-зависимости пользователя

    :param is_verified: если True, пользователь должен быть верифицирован
    :param is_superuser: если True, пользователь должен быть админом
    :param websocket_mode: если True, использовать WebSocket-режим, иначе HTTP-режим
    :return: FastAPI-зависимость пользователя (callable)
    """

    async def token_dependency(
            bearertoken: str | None = Depends(oauth2_scheme),
            querytoken: str | None = None,
    ):
        if websocket_mode and querytoken is not None:
            return querytoken
        return bearertoken

    async def current_user_dependency(
            token: str = Depends(token_dependency),
            db: AsyncSession = Depends(get_async_session),
    ):
        """
        Возвращает аутентифицированного пользователя, если аутентификация успешна

        :param token: JWT access token
        :param db: AsyncSession
        :return: ORM-объект User или None, если websocket_mode=True и аутентификация провалена
        :raise HTTPException: если websocket_mode=False и аутентификация провалена
        """

        try:
            payload = decode_jwt(token, secret=config.JWT_SECRET_KEY)
            expire_datetime = payload['exp']
        except Exception:
            if websocket_mode:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='BAD_TOKEN',
            )

        try:
            if datetime.fromtimestamp(expire_datetime) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='EXPIRED_TOKEN',
                )

            email = payload.get('email')
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='BAD_TOKEN',
                )

            user = await UserService(db).get_user_by_email(email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='USER_NOT_FOUND',
                )
            if is_verified and not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='USER_NOT_VERIFIED',
                )
            if is_superuser and not user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='FORBIDDEN',
                )
        except HTTPException as e:
            if websocket_mode:
                return None
            raise e

        return user

    return current_user_dependency
