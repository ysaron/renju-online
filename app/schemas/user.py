import uuid
from datetime import datetime

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import BaseModel


class UserRead(BaseUser[uuid.UUID]):
    name: str
    joined: datetime


class UserCreate(BaseUserCreate):
    name: str


class UserUpdate(BaseUserUpdate):
    name: str


class UserSchema(BaseModel):
    id: uuid.UUID
    name: str
