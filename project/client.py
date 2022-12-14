if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import time
import threading

from project.utils.config import *
from project.utils.utils import make_message, handle_response, client_send_message_loop, parse_start_arguments
from project import logs


async def tcp_client(host: str, port: int):
    """
    TCP client handler. Connects to async server at host:port.
    Reads data from buffer and processes with handle_response() from utils.
    Sends message using JIM protocol, using Message class as action definer for server.
    """
    logs.ClientLoggerObject.logger.info(msg=f'Connecting to: {host}:{port}')
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
    except ConnectionRefusedError:
        print('Remote server is not responding')
        logs.ClientLoggerObject.logger.info('Remote server is not responding')
        return -1

    try:
        while True:
            try:
                username_input = input(LOGIN_MESSAGE).strip()

                if username_input == '/quit':
                    writer.write(make_message(Message.quit))
                    raise KeyboardInterrupt

                # TODO username verification. No spaces
                elif '/register' in username_input.lower():
                    username_input = username_input.partition('/register')[-1].strip()
                    if len(username_input) > 3:
                        user_password = input('Select password: ').strip()
                        user_password_2 = input('Repeat password: ').strip()
                        if user_password == user_password_2:
                            user_login_data = {f'{USER}': {USERNAME: username_input, PASSWORD: user_password}}
                            writer.write(make_message(Message.register, **user_login_data))
                        else:
                            print('Passwords should be similar')
                            continue
                    else:
                        print(f'Name {username_input} is too short, should be > 3 letters')
                        continue

                elif '/ping' in username_input.lower():
                    writer.write(make_message(Message.ping))
                    await writer.drain()
                    _, message = handle_response(await reader.read(PACKAGE_SIZE))
                    print(message)
                    continue

                else:
                    user_password = input(f'{PASSWORD}: ').strip()
                    user_login_data = {f'{USER}': {USERNAME: username_input, PASSWORD: user_password}}
                    writer.write(make_message(Message.authenticate, **user_login_data))

                await writer.drain()

                permit, message = handle_response(await reader.read(PACKAGE_SIZE))
                print(message)
                if permit:
                    print(f'Logging as {username_input}...')
                    logs.ClientLoggerObject.logger.info(msg=f"Logging as '{username_input}' ...")
                    break

            except (KeyboardInterrupt, ConnectionResetError) as login_drop_err:
                raise ConnectionResetError(login_drop_err)

            time.sleep(1)

        logs.ClientLoggerObject.logger.info(msg='Starting input thread')
        t2 = threading\
            .Thread(target=asyncio.run, args=(client_send_message_loop(writer, username_input),),
                    daemon=False)
        t2.start()

        while True:
            server_response = await reader.read(PACKAGE_SIZE)
            status, message = handle_response(server_response)
            print(f'\n{message}\n>> ')

    except ConnectionResetError as connection_reset:
        logs.ClientLoggerObject.logger.warning(msg=connection_reset)

        return 1


async def main():
    arguments = parse_start_arguments()
    task = asyncio.create_task(tcp_client(arguments.addr, arguments.port))
    return await asyncio.gather(task)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt as e:
        logs.ClientLoggerObject.logger.info(msg='Connection terminated')
