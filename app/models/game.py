from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Boolean, Table, SmallInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
from sqlalchemy.dialects import postgresql as psql

from app.core.db.session import Base
from app.enums.game import PlayerRoleEnum, GameStateEnum, PlayerResultEnum, PlayerResultReasonEnum
from .mixins import UuidIdMixin


game_mode_m2m = Table(
    'game_mode_m2m',
    Base.metadata,
    Column('game_id', ForeignKey('game.id', ondelete='CASCADE'), primary_key=True),
    Column('gamemode_id', ForeignKey('gamemode.id', ondelete='CASCADE'), primary_key=True),
)


class PlayerRole(Base):
    """
    Association Object

    https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#association-object
    """
    player_id = Column(psql.UUID(as_uuid=True), ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    game_id = Column(psql.UUID(as_uuid=True), ForeignKey('game.id', ondelete='CASCADE'), primary_key=True)
    role = Column(
        Enum(PlayerRoleEnum, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PlayerRoleEnum.first.value,
    )
    ready = Column(Boolean, default=False)
    can_move = Column(Boolean, default=False)

    # One To One (PlayerResult)
    result_id = Column(Integer, ForeignKey('playerresult.id', ondelete='CASCADE'))
    result = relationship(
        'PlayerResult',
        back_populates='pr',
        lazy='selectin',
        cascade='save-update, merge, delete, delete-orphan',
        single_parent=True,
    )

    game = relationship('Game', back_populates='players', lazy='selectin')
    player = relationship('User', back_populates='games', lazy='selectin')


class Game(UuidIdMixin, Base):
    # m2m Intermediate (User)
    players = relationship(
        'PlayerRole',
        back_populates='game',
        lazy='selectin',
        cascade='save-update, merge, delete, delete-orphan',
    )

    state = Column(Enum(GameStateEnum), nullable=False, default=GameStateEnum.created)
    created_at = Column(DateTime(timezone=True), default=func.now())
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    is_private = Column(Boolean, default=False)

    # m2m (GameMode)
    modes = relationship('GameMode', secondary=game_mode_m2m, back_populates='games', lazy='selectin')

    # One To Many (Move)
    moves = relationship('Move', back_populates='game', lazy='selectin')

    time_limit = Column(Integer)
    board_size = Column(Integer, default=15)
    classic_mode = Column(Boolean, default=False)
    with_myself = Column(Boolean, default=False)
    num_players = Column(Integer, default=2)
    board = Column(String)


class PlayerResult(Base):
    id = Column(Integer, primary_key=True)
    result = Column(Enum(PlayerResultEnum))
    reason = Column(Enum(PlayerResultReasonEnum))

    # One To One (PlayerRole)
    pr = relationship('PlayerRole', back_populates='result', uselist=False, lazy='selectin')


class GameMode(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True)
    time_limit = Column(Integer, default=None)
    board_size = Column(Integer, default=None)
    classic_mode = Column(Boolean, default=None)
    with_myself = Column(Boolean, default=None)
    three_players = Column(Boolean, default=None)
    is_active = Column(Boolean, default=False)
    dev = Column(Boolean, default=False)

    # m2m (Game)
    games = relationship('Game', secondary=game_mode_m2m, back_populates='modes', lazy='selectin')


class Move(Base):
    id = Column(Integer, primary_key=True)

    # Many To One (Game)
    game_id = Column(psql.UUID(as_uuid=True), ForeignKey('game.id', ondelete='CASCADE'))
    game = relationship('Game', back_populates='moves', lazy='selectin')

    role = Column(
        Enum(PlayerRoleEnum, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PlayerRoleEnum.first.value,
    )
    x = Column(SmallInteger)
    y = Column(SmallInteger)
