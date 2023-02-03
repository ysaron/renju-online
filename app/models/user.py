from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import relationship

from app.core.db.session import Base
from .game import PlayerRole, Move, PlayerResult
from .mixins import UuidIdMixin


class User(UuidIdMixin, Base):
    email = Column(String(255), unique=True)
    name = Column(String(40), unique=True)
    hashed_password = Column(String(255))
    joined = Column(DateTime(timezone=True), default=func.now())
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # One to Many
    games = relationship(PlayerRole, back_populates='player', lazy='selectin')
    # moves = relationship(Move, back_populates='player', lazy='selectin')
    # victories = relationship(GameResult, back_populates='winner')
