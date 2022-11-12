
from fastapi import APIRouter, Depends, Body, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.core.db.deps import AsyncSession, get_async_session
from app.core import exceptions
from app.schemas.user import UserRead, UserCreate, TokenResponse
from app.models.user import User
from .services import UserService
from .deps import get_current_user_dependency

auth_router = APIRouter()
users_router = APIRouter()
get_current_user = get_current_user_dependency(is_verified=True)


@auth_router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    try:
        user = await UserService(db).create_user(user_data)
    except exceptions.PasswordTooShort:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='PASSWORD_TOO_SHORT',
        )
    except exceptions.PasswordInsecure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='PASSWORD_INSECURE',
        )
    except exceptions.UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='REGISTER_USER_ALREADY_EXISTS',
        )
    return user


@auth_router.post('/request-verify-token', status_code=status.HTTP_202_ACCEPTED)
async def request_verification(
        email: EmailStr = Body(..., embed=True),
        db: AsyncSession = Depends(get_async_session),
):
    await UserService(db).send_verify_token(email)


@auth_router.post('/verify', status_code=status.HTTP_204_NO_CONTENT)
async def verify(
        token: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_async_session),
):
    try:
        await UserService(db).verify_user(token)
    except (exceptions.JWTDecodeError, exceptions.UserNotExists):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='VERIFY_USER_BAD_TOKEN',
        )


@auth_router.post('/login', response_model=TokenResponse)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_session),
):
    try:
        token_data = await UserService(db).login(email=EmailStr(form_data.username), password=form_data.password)
    except exceptions.UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='LOGIN_BAD_CREDENTIALS',
        )
    except exceptions.UserNotVerified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='LOGIN_USER_NOT_VERIFIED',
        )
    except exceptions.BadCredentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='LOGIN_BAD_CREDENTIALS',
        )
    return token_data


@auth_router.post('/forgot-password', status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
        email: EmailStr = Body(..., embed=True),
        db: AsyncSession = Depends(get_async_session),
):
    await UserService(db).forgot_password(email)


@auth_router.post('/reset-password', status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
        token: str = Body(..., embed=True),
        password: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_async_session),
):
    try:
        await UserService(db).reset_password(token, password)
    except (exceptions.JWTDecodeError, exceptions.UserNotExists):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='VERIFY_USER_BAD_TOKEN',
        )
    except exceptions.PasswordTooShort:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='PASSWORD_TOO_SHORT',
        )
    except exceptions.PasswordInsecure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='PASSWORD_INSECURE',
        )


@users_router.get('/me', response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    return user
