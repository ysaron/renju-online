from typing import Any

from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    subject: str
    email: list[EmailStr] | list[str]
    body: dict[str, Any]
    template: str
