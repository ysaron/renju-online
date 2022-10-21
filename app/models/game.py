from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Boolean, Table, SmallInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
from sqlalchemy.dialects import postgresql as psql

from app.core.db.session import Base
from .mixins import UuidIdMixin
from .enums import PlayerRoleEnum, GameStateEnum, GameResultEnum, GameResultCauseEnum


game_mode_m2m = Table(
    'game_mode_m2m',
    Base.metadata,
    Column('game_id', ForeignKey('game.id'), primary_key=True),
    Column('gamemode_id', ForeignKey('gamemode.id'), primary_key=True),
)


class PlayerRole(Base):
    """
    Association Object

    https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#association-object
    """
    player_id = Column(psql.UUID, ForeignKey('user.id'), primary_key=True)
    game_id = Column(psql.UUID, ForeignKey('game.id'), primary_key=True)
    role = Column(
        Enum(PlayerRoleEnum, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PlayerRoleEnum.first.value,
    )

    game = relationship('Game', back_populates='players')
    player = relationship('User', back_populates='games')


class Game(UuidIdMixin, Base):
    # m2m (User)
    players = relationship('PlayerRole', back_populates='game')

    state = Column(Enum(GameStateEnum), nullable=False, default=GameStateEnum.created)
    created_at = Column(DateTime(timezone=True), default=func.now())
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    is_private = Column(Boolean, default=False)

    # One To One (GameResult)
    result = relationship('GameResult', back_populates='game', uselist=False)

    # m2m (GameMode)
    modes = relationship('GameMode', secondary=game_mode_m2m, back_populates='games')

    # One to many (Move)
    moves = relationship('Move', back_populates='game')


class GameResult(Base):
    id = Column(Integer, primary_key=True)
    result = Column(Enum(GameResultEnum))
    cause = Column(Enum(GameResultCauseEnum))

    # One To One (Game)
    game_id = Column(psql.UUID, ForeignKey('game.id'))
    game = relationship('Game', back_populates='result')


class GameMode(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True)
    time_limit = Column(Integer)
    board_size = Column(Integer)
    classic_mode = Column(Boolean)
    with_myself = Column(Boolean)

    # m2m (Game)
    games = relationship('Game', secondary=game_mode_m2m, back_populates='modes')


class Move(Base):
    id = Column(Integer, primary_key=True)

    # Many to One (Game)
    game_id = Column(psql.UUID, ForeignKey('game.id'))
    game = relationship('Game', back_populates='moves')

    # Many to One (User)
    player_id = Column(psql.UUID, ForeignKey('user.id'))
    player = relationship('User', back_populates='moves')

    x_coord = Column(SmallInteger)
    y_coord = Column(SmallInteger)
