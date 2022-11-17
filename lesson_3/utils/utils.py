import json
import datetime

from .config import *


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


def is_authorized(username, authorized):
    print(f'UTILS | {authorized = }')
    return True
