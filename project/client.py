import asyncio
import argparse
import time
import threading


from project.utils.config import *
from project.utils.utils import make_message, handle_response, client_send_message_loop
from project import logs


async def tcp_client(host: str, port: int):
    logs.ClientLoggerObject.logger.info(msg=f'Connecting to: {host}:{port}')
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
    except ConnectionRefusedError:
        logs.ClientLoggerObject.logger.info('Remote server is not responding')
        return -1

    try:
        while True:
            username_input = 'u2' if DEBUG else input('username: ').strip()
            user_password = 'password' if DEBUG else input('password: ').strip()

            if username_input == 'quit':
                writer.write(make_message(Message.quit))
                return -1
            user_login_data = {
                'user': {USERNAME: username_input,
                         PASSWORD: user_password}}

            writer.write(make_message(Message.authenticate, **user_login_data))
            await writer.drain()

            permit, message = handle_response(await reader.read(PACKAGE_SIZE))
            if permit:
                logs.ClientLoggerObject.logger.info(msg=f'Logging as {username_input}...')
                break

            time.sleep(1)

        logs.ClientLoggerObject.logger.info(msg='Starting input thread')
        t2 = threading\
            .Thread(target=asyncio.run, args=(client_send_message_loop(writer, user_login_data['user']['username']), ),
                    daemon=True)
        t2.start()

        while True:
            server_response = await reader.read(PACKAGE_SIZE)
            _, message = handle_response(server_response)
            await asyncio.sleep(0.1)

    except ConnectionResetError as connection_error:
        logs.ClientLoggerObject.logger.error(msg=connection_error)

    return 1


async def main():
    argument_parser = argparse.ArgumentParser(description='Server start parameters')
    argument_parser.add_argument('-hs', '--host', type=str, dest='host', help=f'Server ip, def = {HOST}', default=HOST)
    argument_parser.add_argument('-p', '--port', type=int, dest='port', default=PORT)

    arguments = argument_parser.parse_args()
    task = asyncio.create_task(tcp_client(arguments.host, arguments.port))

    return await asyncio.gather(task)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt as e:
        logs.ClientLoggerObject.logger.info(msg='Connection terminated')
        loop.close()
