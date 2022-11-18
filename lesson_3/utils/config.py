__all__ = 'Status', 'Message', 'ACTION', 'ENCODING', 'PACKAGE_SIZE', \
          'HOST', 'PORT', 'PASSWORD_SALT', 'TIME', 'USER', 'USERNAME', 'PASSWORD'

from enum import Enum, auto


class Status(Enum):
    OK = 200
    MovedPermanently = 301
    MovedTemporary = 302
    NotAuthorized = 401
    NotFound = 404
    Conflict = 409
    IAmATeapot = 418


class Message(Enum):
    authenticate = auto()
    error = auto()
    msg = auto()
    probe = auto()
    presence = auto()
    join = auto()
    leave = auto()
    quit = auto()


DEBUG = False

ACTION = 'action'
ENCODING = 'utf-8'
TIME = 'time'
USER = 'user'
USERNAME = 'username'
PASSWORD = 'password'

PACKAGE_SIZE = 604  # Max package size in bytes

HOST = '192.168.0.103'
PORT = 4444

PASSWORD_SALT = 'a1e0b9ed02d0719c313114ae83b93dfb2e48d7e99a7624af894aaa81205f44d1'
