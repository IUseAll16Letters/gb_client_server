import asyncio
import time
import threading

if __name__ == '__main__':
    from utils.config import *
    from utils.utils import make_message, handle_response, client_send_message_loop
else:
    from project.utils.config import *
    from project.utils.utils import make_message, handle_response, client_send_message_loop


async def tcp_client(host: str, port: int):
    print(f'Connecting to: {host}:{port}')
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
    except ConnectionRefusedError:
        print('Remote server is not responding')
        return -1

    try:
        while True:
            username_input = 'u2' if DEBUG else input('username: ').strip()
            user_password = 'password' if DEBUG else input('password: ').strip()
            if username_input == 'quit':
                writer.write(make_message(Message.quit))
                return
            user_login_data = {
                'user': {'username': username_input,
                         'password': user_password}}

            writer.write(make_message(Message.authenticate, **user_login_data))
            await writer.drain()

            permit, message = handle_response(await reader.read(PACKAGE_SIZE))
            print(f'MESAGE = {message}')
            if permit:
                print('Logging ...')
                break

            time.sleep(1)

        t2 = threading.Thread(target=asyncio.run,
                              args=(client_send_message_loop(
                                  writer,
                                  user_login_data['user']['username']),
                              ))
        t2.start()

        while True:
            server_response = await reader.read(PACKAGE_SIZE)
            _, message = handle_response(server_response)
            print(f'{message = }')
            await asyncio.sleep(0.1)

    except ConnectionResetError:
        print('Server has dropped connection')
        asyncio.get_event_loop().close()

    return 1


async def main():
    task = asyncio.create_task(tcp_client(HOST, PORT))
    return await asyncio.gather(task)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    try:
        loop.run_until_complete(main())
        # asyncio.run(main())
    except KeyboardInterrupt as e:
        print('\nConnection terminated')
