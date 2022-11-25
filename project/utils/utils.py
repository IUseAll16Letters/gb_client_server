import json
import datetime
import time

from asyncio import StreamWriter
from hashlib import sha256
from typing import Tuple, Optional, Dict

if __name__ == '__main__':
    from config import *
else:
    from project.utils.config import *


class AuthorizationError(ConnectionError):
    pass


def make_message(message_type: Message, **kwargs):
    message_body = {**kwargs}

    if message_type is Message.presence:
        message_body.update({'type': 'status', })

    message_body.update({ACTION: message_type.value})
    message_body.update({TIME: datetime.datetime.now().timestamp()})

    print(f'CLI | UTL | Make message | {message_body}')
    return json.dumps(message_body, ensure_ascii=False, sort_keys=True).encode(ENCODING)


def generate_response_message(code: Status, **kwargs):
    message_body = {"response": code.value}
    message_body.update(**kwargs)

    return json.dumps(message_body, ensure_ascii=False).encode(ENCODING)


async def handle_request(message: bytes, writer: StreamWriter, authorized: Optional[Dict[str, StreamWriter]] = None,
                         db_object: dict = None, test_kwargs: dict = None):
    print(f"HANDLE REQUEST | {message = }")
    if not message:
        raise ConnectionResetError

    message: dict = json.loads(message.decode(ENCODING))
    request_action = Message(message.get('action'))

    if request_action is Message.quit:
        if not test_kwargs:
            print(f'Client {writer.get_extra_info("peername")} wants to quit')
            writer.close()
        else:
            print('\033[33mWarning! server is running in test mode\033[0m')
        return 0

    elif request_action is Message.authenticate:
        print("HANDLE AUTH")
        if DEBUG and not db_object:
            db_object = get_database_object('../db.txt')

        if is_authorized(message, authorized) or authorize(message, db_object, authorized, writer):
            if not test_kwargs:
                writer.write(generate_response_message(Status.OK, **{"message": 'Authorized'}))
                await writer.drain()
            return {"user": message[USER][USERNAME]}
        else:
            print('Cant authorized')
            writer.write(generate_response_message(Status.NotAuthorized, **{"error": 'Wrong user or password'}))
            await writer.drain()
            time.sleep(1)
            return -1

    elif request_action is Message.msg:
        send_to = message['to']
        if send_to in authorized:
            send_to_stream_writer = authorized.get(send_to)
            print(f'SENDING TO: {send_to} || {authorized.get(send_to)}')
            send_to_stream_writer.write(json.dumps(message).encode(ENCODING))
            await send_to_stream_writer.drain()
            return 0
        else:
            writer.write(make_message(Message.error, **{"error": 'User is not logged in'}))
            await writer.drain()
            return -1

    elif request_action is Message.presence:
        writer.write(generate_response_message(Status.OK))
        return 0

    elif DEBUG and test_kwargs and request_action is Message.shutdown:
        event = test_kwargs.get('event')
        print(id(event))
        event.set()
        return 1

    elif request_action is Message.ping:
        ping = f"{round(datetime.datetime.now().timestamp() - message.get('time') - 0.5, 5)} s"
        writer.write(generate_response_message(Status.OK, **{'ping': ping}))
        await writer.drain()
        return 0

    elif request_action is Message.coffee:
        writer.write(generate_response_message(Status.IAmATeapot, **{'message': "Server is a teapot"}))
        return 0


def handle_response(server_response: bytes) -> Tuple[bool, str]:
    print(f'UTL | CLI | {server_response = }')
    if not server_response:
        raise ConnectionResetError('Server has disconnected')

    response_data: dict = json.loads(server_response.decode(ENCODING))

    response_code = response_data.get('response')
    if response_code:
        status = Status(response_code)
        if status is Status.NotAuthorized:
            return False, f'Wrong user data'
        elif (status is Status.OK or status is Status.IAmATeapot) and 'from' not in response_data:
            return True, ' | '.join(f'{k}: {v}' for k, v in response_data.items())
        elif status is Status.NotAuthorized:
            return False, response_data['error']

    elif Message(response_data.get('action')) is Message.msg:
        return True, f"from {response_data['from']}: {response_data['message']}"
    else:
        return False, 'err'


def get_database_object(file_path: str) -> dict:
    users_data = {}
    with open(file_path, 'r', encoding=ENCODING) as db:
        for line in db.readlines():
            username, password = line.split(':')
            users_data.update({username.strip(): password.strip()})

    return users_data


def make_secure_password(password: str) -> str:
    return sha256((password + PASSWORD_SALT).encode(ENCODING)).hexdigest().upper()


def verify_password(username: str, password: str, db_object: dict) -> bool:
    print("VERIFY")
    password_hash = make_secure_password(password)
    user_password = db_object.get(username)
    return user_password == password_hash


def get_user_data_from_set(user_dataset: dict) -> Tuple[str, str]:
    return (user_dataset[USER][USERNAME], user_dataset[USER][PASSWORD])


# @логаем.debug
def authorize(user_data: dict, db_object: dict, authorized: dict, writer):
    print('AUTHORIZE')
    try:
        username, password = get_user_data_from_set(user_data)
        if any((username, password)) and verify_password(username, password, db_object):
            authorized.update({username: writer})
            print(f'User "{username}" authorized, {authorized.keys() = }')
            return True
        else:
            raise AuthorizationError(f"Wrong password for: {username}")

    except AuthorizationError as e:
        print(e)
        return False


def is_authorized(user_data: dict, authorized: dict):
    print('IS AUTHORIZED')
    if get_user_data_from_set(user_data)[0] in authorized:
        print(f'User is already authorized\n{authorized = }')
        return True
    return False


async def client_send_message_loop(writer, username: str):
    print("Type 'quit' in username to leave the chat")
    while True:
        try:
            message_to = input('Send to >> ')
            if message_to == 'quit':
                writer.write(make_message(Message.quit))
                return
            buffer = input("Message >> ")
            writer.write(make_message(Message.msg, **{'message': buffer, 'from': username, 'to': message_to}))
            await writer.drain()
            time.sleep(0.25)
        except UnicodeDecodeError:
            return -1
        except RuntimeError:
            return -1


if __name__ == '__main__':
    print(get_database_object("../db.txt"))
    rsp = generate_response_message(Status.OK, **{"alert": 'Well connected'})
    print(make_secure_password('test_password'))
    print(handle_response(rsp))
    print(make_message(
        Message.msg,
        **{'from': 'Herasimu', 'to': 'Santa-Claus', 'message': "Hello santa!"}))
