from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql.expression import func

from app.core.db.session import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    name = Column(String(40), unique=True)
    joined = Column(DateTime(timezone=True), default=func.now())
