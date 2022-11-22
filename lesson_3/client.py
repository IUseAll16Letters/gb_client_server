import asyncio
import time
import threading

from utils.config import PACKAGE_SIZE, Message, HOST, PORT
from utils.utils import make_message, handle_response, client_send_message_loop


async def tcp_client(host: str, port: int):
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
    except ConnectionRefusedError:
        print('Remote server is not responding')
        return -1

    try:
        while True:
            username_input = input('username: ')
            if username_input == 'quit':
                writer.write(make_message(Message.quit))
                return
            user_login_data = {
                'user': {'username': username_input,
                         # 'password': input('password: '), }}
                         # 'user': {'username': 'user_1',
                         'password': 'password'}}

            writer.write(make_message(Message.authenticate, **user_login_data))
            await writer.drain()

            permit, message = handle_response(await reader.read(PACKAGE_SIZE))
            print(f'MESAGE = {message}')
            if permit:
                print('Logging ...')
                break
            time.sleep(1)

        t2 = threading.Thread(target=asyncio.run,
                              args=(client_send_message_loop(writer, user_login_data['user']['username']), ))
        t2.start()
        while True:
            server_response = await reader.read(PACKAGE_SIZE)
            _, message = handle_response(server_response)
            print(message)
            await asyncio.sleep(0.1)

    except ConnectionResetError:
        print('Server has dropped connection')


async def main():
    task = asyncio.create_task(tcp_client(HOST, PORT))
    await asyncio.gather(task)


if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
        # asyncio.run(main())
    except KeyboardInterrupt:
        print('\nConnection terminated')
