import uuid
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    name: str = Field(..., max_length=40, description='Public user name')

    class Config:
        orm_mode = True


class UserRead(UserBase):
    id: uuid.UUID
    joined: datetime = Field(..., description='Registration date')
    email: EmailStr


class UserCreate(UserBase):
    email: EmailStr = Field(..., description='Email used for authentication')
    password: str


class UserCreateProgrammatically(UserCreate):
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False


class UserInDb(UserBase):
    email: EmailStr
    hashed_password: str
    joined: datetime = Field(..., description='Registration date')
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False


class UserUpdate(UserBase):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
