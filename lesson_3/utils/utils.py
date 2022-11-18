import json
import datetime
import threading
import time

from asyncio import StreamWriter
from hashlib import sha256
from typing import Tuple, Optional, Dict

if __name__ == '__main__':
    from config import *
else:
    from .config import *


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


async def handle_message(
        message: bytes,
        writer: StreamWriter,
        authorized: Optional[Dict[str, StreamWriter]] = None
):
    print(f"HANDLE MESSAGE | {message = }")
    if not message:
        raise ConnectionResetError

    message = json.loads(message.decode(ENCODING))

    if Message(message.get('action')) is Message.quit:
        print(f'Client {writer.get_extra_info("peername")} wants to quit')
        writer.close()

    elif Message(message.get('action')) is Message.authenticate:
        if is_authorized(message, authorized) or authorize(message, get_database("db.txt"), authorized, writer):
            writer.write(generate_response_message(Status.OK, **{"message": 'Well connected'}))
            await writer.drain()
            return {"user": message[USER][USERNAME]}
        else:
            print('Is not authorized')
            writer.write(generate_response_message(Status.NotAuthorized, **{"error": 'Wrong user or password'}))
            await writer.drain()
            time.sleep(1)  # blocking here

    elif Message(message.get('action')) is Message.msg:
        send_to = message['to']
        if send_to in authorized:
            print(f'SENDING TO: {send_to} || {authorized.get(send_to)}')
            authorized.get(send_to).write(json.dumps(message).encode(ENCODING))
        else:
            writer.write(make_message(Message.error, **{"error": 'User is not logged in'}))
            await writer.drain()


def handle_response(server_response: bytes) -> Tuple[bool, str]:
    print(f'UTL | CLI | {server_response = }')
    if not server_response:
        raise ConnectionResetError('Server has disconnected')

    response_data: dict = json.loads(server_response.decode(ENCODING))
    try:
        status = response_data.get('response')
        if status and Status(status) is Status.OK:
            return True, response_data['message']
        elif Message(response_data.get('action')) is Message.msg:
            return True, f"from {response_data['from']}: {response_data['content']}"
        else:
            return False, response_data['error']
    except KeyError:
        print(f'Incorrect message: {response_data}')  # logger
        return False, ''


def get_database(file_path: str) -> dict:
    users_data = {}
    with open(file_path, 'r', encoding=ENCODING) as db:
        for line in db.readlines():
            username, password = line.split(':')
            users_data.update({username.strip(): password.strip()})

    return users_data


def initialize():
    pass


def make_secure_password(password: str) -> str:
    return sha256((password + PASSWORD_SALT).encode(ENCODING)).hexdigest().upper()


def verify_password(username: str, password: str, db_object: dict) -> bool:
    print("VERIFY")
    password_hash = make_secure_password(password)
    user_password = db_object.get(username)
    return user_password == password_hash


def get_user_data_from_set(user_dataset: dict) -> Tuple[str, str]:
    try:
        return (user_dataset[USER][USERNAME], user_dataset[USER][PASSWORD])
    except KeyError:
        print("Wrong data set passed")
        return ('', '')


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
    if user_data.get(USER).get(USERNAME) in authorized:
        print(f'User is already authorized\n{authorized = }')
        return True
    return False


async def client_send_message_loop(writer, username: str):
    print("Type 'quit' in username to leave the chat")
    while True:
        message_to = input('Send to >> ')
        if message_to == 'quit':
            writer.write(make_message(Message.quit))
            return
        buffer = input("Content >> ")
        writer.write(make_message(Message.msg, **{'content': buffer, 'from': username, 'to': message_to}))
        await writer.drain()
        time.sleep(0.25)


if __name__ == '__main__':
    print(get_database("../db.txt"))
    rsp = generate_response_message(Status.OK, **{"alert": 'Well connected'})
    print(make_secure_password('s'))
    print(handle_response(rsp))
