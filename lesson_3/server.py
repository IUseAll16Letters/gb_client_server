import asyncio
import time

from asyncio.streams import StreamWriter, StreamReader
from utils.config import *
from utils.utils import handle_message, get_database


async def handler(reader: StreamReader, writer: StreamWriter):
    print(f'Connection from {writer.get_extra_info("peername")} | waiting authorize')
    username = None
    try:
        while True:
            request = await reader.read(PACKAGE_SIZE)
            print(f'REQUEST | {request = }')
            resp_data = await handle_message(message=request, writer=writer, authorized=authorized)
            if resp_data and resp_data.get('user') is not None:
                username = resp_data.get('user')

            time.sleep(1)

    except ConnectionResetError as e:
        if username:
            print(f'User "{username}" disconnected')
            try:
                authorized.pop(username)
            except KeyError as k_e:
                print(f'Server error | {username} {writer.get_extra_info("peername")} has already left')
        else:
            print(f"{writer.get_extra_info('peername')} has disconnected without authorization")

        writer.close()


async def main() -> None:
    server = await asyncio.start_server(
        handler, HOST, PORT)

    async with server:
        print(f'Listening at {HOST}:{PORT}')
        await server.serve_forever()


if __name__ == '__main__':
    database_users = get_database("db.txt")
    authorized = dict()
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print('Server closing')
