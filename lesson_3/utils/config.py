from enum import Enum, auto
# убрать из глобального импорта


class Status(Enum):
    OK = 200
    NotFound = 404
    MovedPermanently = 301
    MovedTemporary = 302


class Message(Enum):
    probe = auto()
    presence = auto()
    quit = auto()


ACTION = 'action'
ENCODING = 'utf-8'

PACKAGE_SIZE = 604  # Max package size in bytes

HOST = '192.168.0.103'
PORT = 4444

PASSWORD_SALT = 'a1e0b9ed02d0719c313114ae83b93dfb2e48d7e99a7624af894aaa81205f44d1'
