import json
import datetime

from hashlib import sha256
from .config import *


class AuthorizationError(ConnectionError):
    pass


def make_message(message_type: Message, **kwargs):
    message_core = {**kwargs}

    if message_type is Message.presence:
        message_core.update({ACTION: message_type.value,
                             'type': 'status',
                             })
    else:
        message_core.update({ACTION: message_type.value})

    message_core.update({'time': datetime.datetime.now().timestamp()})

    print(message_core)
    return json.dumps(message_core, ensure_ascii=False).encode(ENCODING)


def handle_message(message: bytes, writer):
    print(f'{message = }')
    message = json.loads(message.decode(ENCODING))

    if Message(message.get('action')) is Message.presence:
        return message

    elif Message(message.get('action')) is Message.quit:
        print('Client wants to quit')
        writer.close()


def initialize():
    pass


def make_secure_password(password: str) -> str:
    return sha256((PASSWORD_SALT + password).encode(ENCODING)).hexdigest().upper()


def verify_password(username: str, password: str, db_object: dict) -> bool:
    password_hash = make_secure_password(password)
    user_password = db_object.get(username).get('password')
    return user_password == password_hash


def get_user_data_from_set(user_dataset: dict):
    try:
        return user_dataset['user']['username']
    except KeyError:
        print("Wrong data set passed")
        return False


def authorize(user_data, db_object):
    try:
        username, password = get_user_data_from_set(user_data), 'password'
        if verify_password(username, password, db_object):
            return True
        else:
            raise AuthorizationError

    except AuthorizationError:
        print("Wrong account, password data")
    return False


def is_authorized(username, authorized):
    print(f'UTILS | {authorized = }')
    return True
