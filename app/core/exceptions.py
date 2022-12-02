class UserNotExists(Exception):
    pass


class UserAlreadyExists(Exception):
    pass


class UserInactive(Exception):
    pass


class UserNotVerified(Exception):
    pass


class UserAlreadyVerified(Exception):
    pass


class InvalidToken(Exception):
    pass


class PasswordTooShort(Exception):
    pass


class PasswordInsecure(Exception):
    pass


class JWTDecodeError(Exception):
    pass


class TokenExpired(Exception):
    pass


class BadCredentials(Exception):
    pass


class NoEmptySeats(Exception):
    pass


class UnfinishedGame(Exception):
    pass


class NoGameFound(Exception):
    pass


class AlreadyInGame(Exception):
    pass
