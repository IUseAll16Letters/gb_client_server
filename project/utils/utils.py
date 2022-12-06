import json
import datetime
import time

from asyncio import StreamWriter
from hashlib import sha256
from typing import Tuple, Optional, Dict, Union
from project.utils.config import *
from project import logs
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


class AuthorizationError(ConnectionError):
    pass


def make_message(message_type: Message, **kwargs):
    message_body = {**kwargs}

    if message_type is Message.presence:
        message_body.update({'type': 'status', })

    message_body.update({ACTION: message_type.value})
    message_body.update({TIME: datetime.datetime.now().timestamp()})

    # print(f'CLI | UTL | Make message | {message_body}')
    return json.dumps(message_body, ensure_ascii=False, sort_keys=True).encode(ENCODING)


@logs.ServerLoggerObject
def generate_response_message(code: Status, **kwargs):
    message_body = {"response": code.value, "time": datetime.datetime.now().timestamp()}
    message_body.update(**kwargs)

    return json.dumps(message_body, ensure_ascii=False).encode(ENCODING)


async def handle_request(message: bytes, writer: StreamWriter, authorized: Optional[Dict[str, StreamWriter]],
                         db_object: Union[dict, AsyncConnection], user):

    print(f"HANDLE REQUEST | {message = }")

    if not message:
        raise ConnectionResetError

    print(f'{authorized.keys() = }')

    message: dict = json.loads(message.decode(ENCODING))
    request_action = Message(message.get('action'))

    if request_action is Message.quit:
        authorized.pop(user)
        logs.ServerLoggerObject.logger.info(msg=f'Client {writer.get_extra_info("peername")} wants to quit')
        await save_connection_data(writer.get_extra_info('peername'), db_object, False)
        writer.close()
        return 0

    elif request_action is Message.register:
        user_created, username = await create_new_user(get_user_data_from_set(message), conn=db_object)
        if user_created:
            writer.write(generate_response_message(Status.OK, **{"message": "Created"}))
        else:
            writer.write(generate_response_message(Status.NotAuthorized, **{"error": 'User already exists'}))
        await writer.drain()

        return 0

    elif request_action is Message.authenticate:
        print("HANDLE AUTH")

        if is_authorized(message, authorized) or await authorize(message, db_object, authorized, writer):
            writer.write(generate_response_message(Status.OK, **{"message": 'Authorized'}))
            await writer.drain()
            await save_connection_data(writer.get_extra_info('peername'), db_object, True)
            return message[USER][USERNAME]
        else:
            logs.ServerLoggerObject.logger.warning('User cant get authorized')
            writer.write(generate_response_message(Status.NotAuthorized, **{"error": 'Wrong user or password'}))
            await writer.drain()
            time.sleep(1)
            return -1

    elif request_action is Message.msg:
        send_to = message['to']
        if send_to in authorized:
            send_to_stream_writer = authorized.get(send_to)
            print(f'SENDING TO: {send_to} || {message["from"]}', message)
            send_to_stream_writer.write(generate_response_message(Status.OK, **message))
            await send_to_stream_writer.drain()
            await save_user_message(from_user=message['from'], to_user=send_to, body=message['message'], conn=db_object)
            return 0
        else:
            writer.write(generate_response_message(Status.NotFound, **{"error": 'User is not logged in'}))
            await writer.drain()
            return 0

    elif request_action is Message.presence:
        writer.write(generate_response_message(Status.OK))
        return 0

    elif request_action is Message.ping:
        ping = f"{round(datetime.datetime.now().timestamp() - message.get('time') - 0.5, 5)} s"
        writer.write(generate_response_message(Status.OK, **{'ping': ping}))
        await writer.drain()
        return 0

    elif request_action is Message.coffee:
        writer.write(generate_response_message(Status.IAmATeapot, **{'message': "Server is a teapot"}))
        logs.ServerLoggerObject.logger.info(msg='Server is a teapot!')
        return 0


def handle_response(server_response: bytes) -> Tuple[bool, str]:
    print(f'UTL | CLI | {server_response = }')
    if not server_response:
        raise ConnectionResetError('Server has disconnected')

    response_data: dict = json.loads(server_response.decode(ENCODING))

    response_code = response_data.get('response')

    status = Status(response_code)
    if status is Status.OK:
        action = response_data.get('action')
        if action is None and response_data.get('message') == 'Created':
            return False, 'User created, now log in'
        elif action is None:
            return True, response_data.get('ping')
        elif action is not None and Message(action) is Message.msg:
            return True, f"from {response_data['from']}: {response_data['message']}"

    elif status is Status.IAmATeapot:
        return True, ' | '.join(f'{k}: {v}' for k, v in response_data.items())
    elif status is Status.NotAuthorized:
        return False, response_data['error']
    else:
        return False, 'Unknown message'


@logs.ServerLoggerObject
def get_database_object(file_path: str) -> dict:
    users_data = {}
    with open(file_path, 'r', encoding=ENCODING) as db:
        for line in db.readlines():
            username, password = line.split(':')
            users_data.update({username.strip(): password.strip()})

    return users_data


@logs.ServerLoggerObject
def make_secure_password(password: str) -> str:
    return sha256((password + PASSWORD_SALT).encode(ENCODING)).hexdigest().upper()


async def verify_password(username: str, password: str, db_object: Union[AsyncConnection, dict]) -> bool:
    password_hash = make_secure_password(password)
    user_password = await db_object.execute(text(f"SELECT password FROM users WHERE username == '{username}'"))
    user_password = user_password.all()
    print(f'USER PASS | {user_password = }')
    if user_password:
        user_password = user_password[0][0]
    else:
        return False

    return user_password == password_hash


def get_user_data_from_set(user_dataset: dict) -> Tuple[str, str]:
    return (user_dataset[USER][USERNAME], user_dataset[USER][PASSWORD])


async def authorize(user_data: dict, db_object: dict, authorized: dict, writer):
    print('CALL | AUTHORIZE', user_data)
    username, password = get_user_data_from_set(user_data)
    try:
        if all((username, password)) and await verify_password(username, password, db_object):
            authorized.update({username: writer})
            print(f'User "{username}" authorized, {authorized.keys() = }')
            return True
        else:
            raise AuthorizationError(f"Wrong password for: {username}")

    except AuthorizationError as e:
        logs.ServerLoggerObject.logger.warning(msg=e)
        return False


@logs.ServerLoggerObject
def is_authorized(user_data: dict, authorized: dict):
    print('CALL | IS AUTHORIZED')
    if get_user_data_from_set(user_data)[0] in authorized:
        logs.ServerLoggerObject.logger.info(f'User is already authorized\n{authorized = }')
        return True
    return False


async def client_send_message_loop(writer, username: str):
    print("Type 'quit' in username to leave the chat")
    while True:
        try:
            message_to = input('Send to >> ')
            if message_to == 'quit':
                writer.write(make_message(Message.quit))
                return 0
            buffer = input("Message >> ")
            writer.write(make_message(Message.msg, **{'message': buffer, 'from': username, 'to': message_to}))
            await writer.drain()
            time.sleep(0.25)
        except KeyboardInterrupt:
            return -1
        except UnicodeDecodeError:
            return -1
        except RuntimeError:
            return -1


async def setup_db(conn: AsyncConnection):
    await conn.execute(text(f'DROP TABLE IF EXISTS connections'))

    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS connections ('
                            f'connection_id INTEGER PRIMARY KEY,'
                            f'pername TEXT,'
                            f'event_at TEXT,'
                            f'is_leaving BOOl)'))

    await conn.execute(text(f'DROP TABLE IF EXISTS users'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS users ('
                            f'user_id INTEGER PRIMARY KEY,'
                            f'username VARCHAR(50),'
                            f'password VARCHAR(100))'))
    if DEBUG:
        for i in range(1, 4):
            await conn.execute(text(f"INSERT INTO users VALUES ({i}, 'u{i}', '{TEST_PASSWORD}')"))

    await conn.execute(text(f'DROP TABLE IF EXISTS user_messages'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS user_messages ('
                            f'message_id INTEGER PRIMARY KEY,'
                            f'from_user VARCHAR(50),'
                            f'to_user VARCHAR(50),'
                            f'body TEXT,'
                            f'created_at TEXT)'))

    await conn.commit()


async def create_new_user(user_data: tuple, conn: AsyncConnection) -> Tuple[bool, str]:
    is_user_created = await conn.execute(text(f"SELECT * FROM users WHERE username == '{user_data[0]}'"))
    is_user_created = is_user_created.all()
    if is_user_created:
        return False, ''

    max_user_id = await conn.execute(text("SELECT MAX(user_id) FROM users"))
    max_user_id = max_user_id.all()[0][0]
    max_user_id = max_user_id + 1 if max_user_id is not None else 1
    print(f'{max_user_id = }', user_data)

    await conn.execute(
        text(f"INSERT INTO users VALUES ('{max_user_id}', '{user_data[0]}', '{make_secure_password(user_data[1])}')"))
    await conn.commit()

    print(user_data)
    return True, user_data[0]


async def save_connection_data(addr_pair: tuple, conn: AsyncConnection, connected: bool = True):
    max_id = await conn.execute(text("SELECT MAX(connection_id) FROM connections"))
    max_id = max_id.all()[0][0]
    max_id = max_id + 1 if max_id is not None else 1
    user_addr = str(addr_pair).replace("'", '')

    await conn.execute(text(f"INSERT INTO connections "
                            f"VALUES ({max_id}, '{user_addr}', '{datetime.datetime.now()}', {connected})"))
    await conn.commit()


async def save_user_message(from_user: str, to_user: str, body: str, conn: AsyncConnection) -> None:
    max_mess_id = await conn.execute(text("SELECT MAX(message_id) FROM user_messages"))
    max_mess_id = max_mess_id.all()[0][0]
    max_mess_id = max_mess_id + 1 if max_mess_id is not None else 1

    await conn.execute(text(f"INSERT INTO user_messages "
                            f"VALUES ({max_mess_id}, '{from_user}',"
                            f" '{to_user}', '{body}', '{datetime.datetime.now()}')"))
    await conn.commit()


if __name__ == '__main__':
    print(get_database_object("../db.txt"))
    rsp = generate_response_message(Status.OK, **{"alert": 'Well connected'})
    print(make_secure_password('test_password'))
    print(handle_response(rsp))
    print(make_message(
        Message.msg,
        **{'from': 'Herasimu', 'to': 'Santa-Claus', 'message': "Hello santa!"}))
