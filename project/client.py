if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

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
            try:
                username_input = input(LOGIN_MESSAGE).strip()

                if username_input == 'quit':
                    writer.write(make_message(Message.quit))
                    raise ConnectionResetError

                elif '/register' in username_input.lower() and \
                        len((username_input := username_input.partition('/register')[-1].strip())) > 3:
                    user_password = input('Select password: ').strip()
                    user_password_2 = input('Repeat password: ').strip()
                    if user_password == user_password_2:
                        user_login_data = {'user': {USERNAME: username_input, PASSWORD: user_password}}
                        writer.write(make_message(Message.register, **user_login_data))
                    else:
                        print('Passwords should be similar')
                        continue
                elif '/ping' in username_input.lower():
                    writer.write(make_message(Message.ping))
                    await writer.drain()
                    _, message = handle_response(await reader.read(PACKAGE_SIZE))
                    print(message)
                    continue
                else:
                    user_password = input('password: ').strip()
                    user_login_data = {'user': {USERNAME: username_input, PASSWORD: user_password}}
                    writer.write(make_message(Message.authenticate, **user_login_data))

                await writer.drain()

                permit, message = handle_response(await reader.read(PACKAGE_SIZE))
                if permit:
                    print(f'Logging as {username_input}...')
                    logs.ClientLoggerObject.logger.info(msg=f"Logging as '{username_input}' ...")
                    break

            except KeyboardInterrupt:
                raise ConnectionResetError

            time.sleep(1)

        logs.ClientLoggerObject.logger.info(msg='Starting input thread')
        t2 = threading\
            .Thread(target=asyncio.run, args=(client_send_message_loop(writer, user_login_data['user']['username']), ),
                    daemon=True)
        t2.start()

        while True:
            server_response = await reader.read(PACKAGE_SIZE)
            _, message = handle_response(server_response)
            print(message + '\n>>> ')
            await asyncio.sleep(0.1)

    except ConnectionResetError as connection_reset:
        logs.ClientLoggerObject.logger.warning(msg=connection_reset)

    return 1


async def main():
    argument_parser = argparse.ArgumentParser(description='Server start parameters')
    argument_parser.add_argument('-a', '--addr', type=str, dest='addr', help=f'Server ip, def = {HOST}', default=HOST)
    argument_parser.add_argument('-p', '--port', type=int, dest='port', default=PORT)

    arguments = argument_parser.parse_args()
    task = asyncio.create_task(tcp_client(arguments.addr, arguments.port))

    return await asyncio.gather(task)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt as e:
        logs.ClientLoggerObject.logger.info(msg='Connection terminated')
        loop.close()
