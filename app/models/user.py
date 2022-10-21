from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import relationship

from app.core.db.session import Base
from .game import PlayerRole, Move, GameResult


class User(SQLAlchemyBaseUserTableUUID, Base):
    name = Column(String(40), unique=True)
    joined = Column(DateTime(timezone=True), default=func.now())

    # One to Many
    games = relationship(PlayerRole, back_populates='player')
    moves = relationship(Move, back_populates='player')
    victories = relationship(GameResult, back_populates='winner')
