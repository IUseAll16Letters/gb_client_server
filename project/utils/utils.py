import argparse
import json
import datetime
import time

from asyncio import StreamWriter
from hashlib import sha256
from typing import Tuple, Optional, Dict, Union

from project.utils.config import *
from project.utils.db_utils import *
from project import logs
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


class AuthorizationError(ConnectionError):
    pass


def make_message(message_type: Message, **kwargs):
    """Message from client to server"""
    message_body = {**kwargs}

    if message_type is Message.presence:
        message_body.update({'type': 'status', })

    message_body.update({ACTION: message_type.value})
    message_body.update({TIME: datetime.datetime.now().timestamp()})

    return json.dumps(message_body, ensure_ascii=False, sort_keys=True).encode(ENCODING)


@logs.ServerLoggerObject
def generate_response_message(code: Status, **kwargs):
    """message from server to client"""
    message_body = {"response": code.value, "time": datetime.datetime.now().timestamp()}
    message_body.update(**kwargs)
    return json.dumps(message_body, ensure_ascii=False).encode(ENCODING)


async def handle_request(message: bytes, writer: StreamWriter, authorized: Optional[Dict[str, StreamWriter]],
                         db_object: AsyncConnection, user):
    """
    message - bytes, message from user in form {action: Message, **kwargs};
    writer - Stream object related to client reader socker;
    authorized  - dict with users currently logged in;
    db_object - Async db connection;
    user - username related to StreamWriter in current coroutine
    Main server requests processor:
        quit - raises ConnectionResetError, stops user streams, removes from authorized.
        register - new user creation if not exists.
        authenticate - auth user, if already authed - checks authorized dict.
        msg - sends message to user or group if send_to stats with '#'.
        create, join, leave, party - group functions. Party shows groups user is joined.
        presence - default message, deprecated.
        ping - check the delay to server in ms, based on time difference
        coffee - check if server is a teapot! very important command!
    """
    if not message:
        raise ConnectionResetError

    message: dict = json.loads(message.decode(ENCODING))
    request_action = Message(message.get('action'))

    if request_action is Message.quit:
        try:
            authorized.pop(user)
        except KeyError:
            raise ConnectionResetError

        logs.ServerLoggerObject.logger.info(msg=f'Client {writer.get_extra_info("peername")} wants to quit')
        await save_connection_data(writer.get_extra_info('peername'), db_object, True)
        writer.close()
        return 0

    elif request_action is Message.register:
        user_created, username_or_404 = await create_new_user(get_user_data_from_set(message), conn=db_object)
        if user_created:
            writer.write(generate_response_message(Status.OK, **{"message": f"Created {username_or_404}"}))
        else:
            writer.write(generate_response_message(Status.NotAuthorized, **{"error": username_or_404}))
        await writer.drain()

        return 0

    elif request_action is Message.authenticate:

        if is_authorized(message, authorized) or await authorize(message, db_object, authorized, writer):
            writer.write(generate_response_message(Status.OK, **{"message": 'Authorized'}))
            await writer.drain()
            await save_connection_data(addr_pair=writer.get_extra_info('peername'), conn=db_object, connected=False)
            return message[USER][USERNAME]
        else:
            logs.ServerLoggerObject.logger.warning(msg=f'User cant get authorized {message}')
            writer.write(generate_response_message(Status.NotAuthorized, **{"error": 'Wrong user or password'}))
            await writer.drain()
            time.sleep(1)
            return -1

    elif request_action is Message.msg:
        send_to, from_user = message['to'], message['from']
        if send_to.startswith('#'):
            send_to = send_to.replace('#', '')
            permit, users_or_404_message = await get_users_group_if_permit(
                group_name=send_to, from_user=from_user, conn=db_object
            )
            if not permit:
                writer.write(generate_response_message(Status.NotFound, **{"error": users_or_404_message}))
                await writer.drain()

            if users_or_404_message:
                await save_user_message(from_user=message['from'], to_user=f"#{send_to}", body=message['message'],
                                        conn=db_object)
            for user in users_or_404_message:
                if user[0] in authorized:
                    send_to_stream = authorized.get(user[0])
                    message.update({'to': user[0]})
                    send_to_stream.write(generate_response_message(Status.OK, **message))
                    await send_to_stream.drain()

        elif send_to in authorized:
            send_to_stream = authorized.get(send_to)
            send_to_stream.write(generate_response_message(Status.OK, **message))
            await send_to_stream.drain()
            await save_user_message(from_user=message['from'], to_user=send_to, body=message['message'], conn=db_object)
            return 0
        else:
            writer.write(generate_response_message(Status.NotFound, **{"error": f'User {send_to} not logged in'}))
            await writer.drain()
            return 0

    elif request_action in (Message.create, Message.join, Message.leave, Message.party):
        is_success, message = await process_group_request(request=request_action, conn=db_object,
                                                          username=message['user'], group_name=message['group'])
        if is_success:
            writer.write(generate_response_message(Status.OK, **{'message': message}))
        else:
            writer.write(generate_response_message(Status.NotAuthorized, **{'error': message}))
        await writer.drain()
        return 0

    elif request_action is Message.presence:
        writer.write(generate_response_message(Status.OK))
        await writer.drain()
        return 0

    elif request_action is Message.ping:
        ping = f"{round((datetime.datetime.now().timestamp() - message.get('time')) * 1000, 2)} ms"
        writer.write(generate_response_message(Status.OK, **{'ping': ping}))
        await writer.drain()
        return 0

    elif request_action is Message.coffee:
        writer.write(generate_response_message(Status.IAmATeapot, **{'message': "Server is a teapot"}))
        logs.ServerLoggerObject.logger.info(msg='Server is a teapot!')
        await writer.drain()
        return 0

    else:
        raise ConnectionResetError('Unknown message, error occurred')


def handle_response(server_response: bytes) -> Tuple[bool, str]:
    """Client handler core logic"""
    if not server_response:
        raise ConnectionResetError('Server has disconnected')

    response_data: dict = json.loads(server_response.decode(ENCODING))

    response_code = response_data.get('response')

    status = Status(response_code)
    if status is Status.OK:
        action = response_data.get('action')
        if action is None and response_data.get('message') is not None:
            message: str = response_data.get('message')
            if message.split()[0] == 'Created':
                return False, 'User created, now log in'
            else:
                return True, message
        elif action is None:
            return True, f"Ping to server: {response_data.get('ping')}"
        elif action is not None and Message(action) is Message.msg:
            return True, f"from {response_data['from']}: {response_data['message']}"

    elif status is Status.IAmATeapot:
        return True, ' | '.join(f'{k}: {v}' for k, v in response_data.items())
    elif status in (Status.NotAuthorized, Status.NotFound):
        return False, response_data['error']
    else:
        return False, 'Unknown message'


@logs.ServerLoggerObject
def get_database_object(file_path: str) -> dict:
    """DEPRECATED"""
    users_data = {}
    with open(file_path, 'r', encoding=ENCODING) as db:
        for line in db.readlines():
            username, password = line.split(':')
            users_data.update({username.strip(): password.strip()})

    return users_data


@logs.ServerLoggerObject
def make_secure_password(password: str) -> str:
    return sha256((password + PASSWORD_SALT).encode(ENCODING)).hexdigest().upper()


async def verify_password(username: str, password: str, db_object: AsyncConnection) -> bool:
    input_password_as_hash = make_secure_password(password)
    user_pass_db = await db_object.execute(
        text("SELECT password FROM users WHERE name == :un"),
        {'un': username}
    )
    user_pass_db = user_pass_db.fetchall()

    if user_pass_db:
        user_password = user_pass_db[0][0]
    else:
        return False
    return user_password == input_password_as_hash


def get_user_data_from_set(user_dataset: dict) -> Tuple[str, str]:
    return (user_dataset[USER][USERNAME], user_dataset[USER][PASSWORD])


async def authorize(user_data: dict, db_object: AsyncConnection, authorized: dict, writer: StreamWriter) -> bool:
    username, password = get_user_data_from_set(user_data)
    try:
        if all((username, password)) and await verify_password(username, password, db_object):
            authorized.update({username: writer})
            return True
        else:
            raise AuthorizationError(f"Wrong password for: {username}")

    except AuthorizationError as e:
        logs.ServerLoggerObject.logger.warning(msg=e)
        return False


@logs.ServerLoggerObject
def is_authorized(user_data: dict, authorized: dict):
    if get_user_data_from_set(user_data)[0] in authorized:
        logs.ServerLoggerObject.logger.info(f'User is already authorized\n{authorized = }')
        return True
    return False


async def client_send_message_loop(writer: StreamWriter, username: str):
    """Client input processor, started in separate thread"""
    print("Type '/quit' in Send to field to leave")
    while True:
        try:
            action_or_send_to = input('Send to >> ')

            if action_or_send_to.strip().lower() == '/quit':
                writer.write(make_message(Message.quit))
                await writer.drain()
                return 0

            # TODO DRY
            elif '/ping' in action_or_send_to.lower():
                writer.write(make_message(Message.ping))

            elif '/create' in action_or_send_to.lower():
                gname = action_or_send_to.partition('/create')[-1].strip()
                writer.write(make_message(Message.create, **{'group': gname, USER: username}))

            elif '/join' in action_or_send_to.lower():
                gname = action_or_send_to.partition('/join')[-1].strip()
                writer.write(make_message(Message.join, **{'group': gname, USER: username}))

            elif '/leave' in action_or_send_to.lower():
                gname = action_or_send_to.partition('/leave')[-1].strip()
                writer.write(make_message(Message.leave, **{'group': gname, USER: username}))

            elif '/party' in action_or_send_to.lower():
                writer.write(make_message(Message.party, **{'group': 'None', USER: username}))

            elif action_or_send_to.lower().strip() == '/help':
                print(HELP_MESSAGE)

            else:
                message_input = input("\nMessage >> ")
                writer.write(make_message(Message.msg,
                                          **{'message': message_input, 'from': username, 'to': action_or_send_to}))
            await writer.drain()
            time.sleep(0.25)

        except KeyboardInterrupt:
            return -1
        except UnicodeDecodeError:
            return -1
        except RuntimeError:
            return -1


async def create_new_user(user_data: tuple, conn: AsyncConnection) -> Tuple[bool, str]:
    username, pwd = user_data[0], user_data[1]
    user_created = await conn.execute(
        text("SELECT * FROM users WHERE name == :un"),
        {'un': username}
    )
    if user_created.all():
        return False, f'User {username} already exist'

    await conn.execute(
        text("INSERT INTO users (name, password) VALUES (:un, :pwd)"),
        {'un': username, 'pwd': make_secure_password(pwd)}
    )
    await conn.commit()
    return True, username


def parse_start_arguments():
    argument_parser = argparse.ArgumentParser(description='Server start parameters')
    argument_parser.add_argument('-a', '--addr', type=str, dest='addr', help=f'Server ip, def = {HOST}', default=HOST)
    argument_parser.add_argument('-p', '--port', type=int, dest='port', default=PORT)

    return argument_parser.parse_args()


if __name__ == '__main__':
    print(get_database_object("../test_db.txt"))
    rsp = generate_response_message(Status.OK, **{"alert": 'Well connected'})
    print(make_secure_password('test_password'))
    print(handle_response(rsp))
    print(make_message(
        Message.msg,
        **{'from': 'Herasimu', 'to': 'Santa-Claus', 'message': "Hello santa!"}))
