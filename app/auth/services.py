from datetime import datetime
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import select, or_

from app.core.db.deps import AsyncSession
from app.core import exceptions
from app.config import config
from app.models.user import User
from app.schemas.user import UserCreate, UserInDb, TokenResponse
from .utils import get_password_hash, generate_jwt, decode_jwt, validate_password, check_password
from app.core.email.sending import send_email
from app.schemas.email import EmailSchema


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.__db = db_session

    async def user_exists(self, user_data: UserCreate) -> bool:
        """ Check if user with this username or email exists """
        stmt = select(User.id).where(or_(
            User.name == user_data.name,
            User.email == user_data.email,
        ))
        user = await self.__db.scalars(stmt)
        return bool(user.first())

    async def get_user_by_email(self, email: EmailStr) -> User:
        stmt = select(User).where(User.email == email)
        user = await self.__db.scalars(stmt)
        return user.first()

    async def get_user_by_id(self, user_id: UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        user = await self.__db.scalars(stmt)
        return user.first()

    async def create_user(self, user_data: UserCreate) -> User:
        """
        :return: User ORM instance
        :raise UserAlreadyExists: if user already exists
        """
        validate_password(user_data)

        if await self.user_exists(user_data):
            raise exceptions.UserAlreadyExists()

        user_in_db = UserInDb(
            **user_data.dict(),
            hashed_password=get_password_hash(user_data.password),
            joined=datetime.utcnow(),
        )
        user = User(**user_in_db.dict())

        self.__db.add(user)
        await self.__db.commit()
        await self.__db.refresh(user)

        return user

    async def send_verify_token(self, email: EmailStr) -> None:
        user = await self.get_user_by_email(email)
        if all([
            user is not None,
            user.is_active,
            not user.is_verified,
        ]):
            token = generate_jwt(
                data={'user_id': str(user.id)},
                secret=config.VERIFICATION_TOKEN_SECRET,
                lifetime_sec=config.ACCESS_TOKEN_EXPIRE_SECONDS,
            )
            email = EmailSchema(
                subject='Email verification',
                email=[user.email],
                body={
                    'title': 'Email verification',
                    'username': user.name,
                    'token': token,
                },
                template='verification_email.html',
            )
            await send_email(email)

    async def verify_user(self, token: str) -> None:
        """
        Set ``user.is_verified = True`` if JWT is valid and user exists

        :param token: JWT containing user_id
        :return: None
        :raise JWTDecodeError:
        :raise UserNotExists:
        """
        try:
            user_id = decode_jwt(token, secret=config.VERIFICATION_TOKEN_SECRET).get('user_id')
        except Exception as e:
            raise exceptions.JWTDecodeError() from e
        if not user_id:
            raise exceptions.JWTDecodeError()

        user = await self.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotExists()
        user.is_verified = True
        await self.__db.commit()

    async def login(self, email: EmailStr, password: str) -> TokenResponse:
        """

        :param email:
        :param password:
        :return:
        :raise UserNotExists:
        :raise UserNotVerified:
        :raise BadCredentials:
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise exceptions.UserNotExists()
        if not user.is_verified:
            raise exceptions.UserNotVerified()
        if not check_password(password, user.hashed_password):
            raise exceptions.BadCredentials()

        access_token = generate_jwt(
            data={'email': user.email},
            secret=config.JWT_SECRET_KEY,
            lifetime_sec=config.ACCESS_TOKEN_EXPIRE_SECONDS,
        )
        return TokenResponse(access_token=access_token, token_type='bearer')

    async def forgot_password(self, email: EmailStr) -> None:
        """ Send token for changing password if the corresponding user exists """
        user = await self.get_user_by_email(email)
        if user is not None:
            token = generate_jwt(
                data={'user_id': str(user.id)},
                secret=config.RESET_PASSWORD_TOKEN_SECRET,
                lifetime_sec=config.ACCESS_TOKEN_EXPIRE_SECONDS,
            )
            email = EmailSchema(
                subject='Changing password',
                email=[user.email],
                body={
                    'title': 'Changing password',
                    'username': user.name,
                    'token': token,
                },
                template='forgot_password_email.html',
            )
            await send_email(email)

    async def reset_password(self, token: str, plain_password: str) -> None:
        try:
            user_id = decode_jwt(token, secret=config.RESET_PASSWORD_TOKEN_SECRET).get('user_id')
        except Exception as e:
            raise exceptions.JWTDecodeError() from e
        if not user_id:
            raise exceptions.JWTDecodeError()

        user = await self.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotExists()

        user_schema = UserCreate(name=user.name, email=user.email, password=plain_password)
        validate_password(user_schema)
        user.hashed_password = get_password_hash(plain_password)
        await self.__db.commit()
