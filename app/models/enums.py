import enum


class PlayerRoleEnum(enum.Enum):
    first = '1'
    second = '2'
    third = '3'


class GameStateEnum(enum.Enum):
    created = 1
    pending = 2
    finished = 3


class GameResultEnum(enum.Enum):
    win = 1
    draw = 2


class GameResultCauseEnum(enum.Enum):
    fair = 'honest victory'
    timeout = 'timeout'
    surrender = 'opponent surrendered'
    no_cells = 'game board is over'
    agreed_draw = 'players agreed to a draw'
