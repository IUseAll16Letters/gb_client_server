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
