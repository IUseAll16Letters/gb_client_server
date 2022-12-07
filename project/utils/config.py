__all__ = [
    'Status', 'Message', 'ACTION', 'ENCODING', 'PACKAGE_SIZE',
    'HOST', 'PORT', 'PASSWORD_SALT', 'TIME', 'USER', 'USERNAME',
    'PASSWORD', 'DEBUG', 'DIR_PATH', 'CLIENT_LOG_LEVEL', 'SERVER_LOG_LEVEL',
    'TEST_PASSWORD', 'LOGIN_MESSAGE'
]

from pathlib import Path
from enum import Enum, auto


DEBUG = False
DIR_PATH = Path(__file__).parent.parent


class Status(Enum):
    OK = 200
    MovedPermanently = 301
    MovedTemporary = 302
    NotAuthorized = 401
    NotFound = 404
    Conflict = 409
    IAmATeapot = 418
    ServiceUnavailable = 503


class Message(Enum):
    authenticate = auto()  # 1
    error = auto()         # 2
    msg = auto()           # 3
    ping = auto()
    presence = auto()
    join = auto()          # 6
    leave = auto()
    quit = auto()          # 8
    register = auto()      # 9

    if DEBUG:
        shutdown = auto()  # 9
        coffee = auto()  # 10


CLIENT_LOG_LEVEL = 10
SERVER_LOG_LEVEL = 10

ACTION = 'action'
ENCODING = 'utf-8'
TIME = 'time'
USER = 'user'
USERNAME = 'username'
PASSWORD = 'password'

PACKAGE_SIZE = 604  # Max package size in bytes

# HOST = '192.168.0.103'
HOST = '127.0.0.1'
PORT = 4444

PASSWORD_SALT = 'a1e0b9ed02d0719c313114ae83b93dfb2e48d7e99a7624af894aaa81205f44d1'
TEST_PASSWORD = 'CCADBC1A760A45EAD104A72A7618E81C7C4F74E6AF336E7F38434519EF0D211A'

LOGIN_MESSAGE = "Enter 'quit' to leave\n" \
                "'/register username' to create new user. Name > 3 letters\n" \
                "or enter your current username: "
