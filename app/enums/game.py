import enum


class PlayerRoleEnum(enum.Enum):
    first = '1'
    second = '2'
    third = '3'
    spectator = '4'


class GameStateEnum(enum.Enum):
    created = 'created'
    pending = 'pending'
    finished = 'finished'


class PlayerResultEnum(enum.Enum):
    win = 1
    lose = 2
    draw = 3


class PlayerResultReasonEnum(enum.Enum):
    fair = 'five in row'
    timeout = 'timeout'
    concede = 'concede'
    disconnect = 'disconnect'
    full_board = 'the board is full'
    tech = 'technical'
    agreement = 'agreement'
