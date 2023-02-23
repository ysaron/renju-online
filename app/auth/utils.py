from datetime import datetime, timedelta
from typing import Any

from jose import jwt

from app.core.exceptions import PasswordTooShort, PasswordInsecure
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def validate_password(user_data: UserCreate) -> None:
    """
    :raise PasswordTooShort: если пароль короче 8 символов
    :raise PasswordInsecure: если пароль слишком похож на имя или емейл
    """

    if len(user_data.password) < 8:
        raise PasswordTooShort()
    if any([
        user_data.password.lower() in user_data.email,
        user_data.password.lower() in user_data.name.lower(),
        user_data.email in user_data.password.lower(),
        user_data.name.lower() in user_data.password.lower(),
    ]):
        raise PasswordInsecure()


def check_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_jwt(
        data: dict[str, Any],
        secret: str,
        lifetime_sec: int | None = None,
        algorithm: str = 'HS256',
) -> str:
    payload = data.copy()
    if lifetime_sec:
        expire = datetime.utcnow() + timedelta(seconds=lifetime_sec)
        payload['exp'] = expire
    return jwt.encode(payload, key=secret, algorithm=algorithm)


def decode_jwt(
        encoded_jwt: str,
        secret: str,
        algorithm: str = 'HS256',
) -> dict:
    return jwt.decode(encoded_jwt, key=secret, algorithms=[algorithm])
