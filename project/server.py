import asyncio
import argparse
import time

from asyncio.streams import StreamWriter, StreamReader
if __name__ == '__main__':
    from utils.config import *
    from utils.utils import handle_request, get_database_object
else:
    from project.utils.config import *
    from project.utils.utils import handle_request, get_database_object


authorized = dict()
try:
    database_users = get_database_object('../db.txt')
except FileNotFoundError:
    database_users = get_database_object('db.txt')


async def handler(reader: StreamReader, writer: StreamWriter):
    print(f'Connection from {writer.get_extra_info("peername")} | waiting authorize')
    username = None
    try:
        while True:
            request = await reader.read(PACKAGE_SIZE)
            print(f'REQUEST | {request = }')
            resp_data = await handle_request(
                message=request,
                writer=writer,
                authorized=authorized,
                db_object=database_users
            )
            # Зачем это тут на каждом сообщении, м?
            if isinstance(resp_data, dict) and resp_data.get('user') is not None:
                username = resp_data.get('user')

            time.sleep(0.5)

    except ConnectionResetError as e:
        if username:
            print(f'User "{username}" disconnected')
            try:
                authorized.pop(username)
                print(authorized.keys())
            except KeyError as k_e:
                print(f'Server error | {username} {writer.get_extra_info("peername")} has already left')

        else:
            print(f"{writer.get_extra_info('peername')} has disconnected without authorization")

    writer.close()


async def main() -> None:
    argument_parser = argparse.ArgumentParser(description='Server start parameters')
    argument_parser.add_argument('-hs', '--host', type=str, dest='host', help=f'Server ip, def = {HOST}', default=HOST)
    argument_parser.add_argument('-p', '--port', type=int, dest='port', default=PORT)

    arguments = argument_parser.parse_args()

    server = await asyncio.start_server(handler, arguments.host, arguments.port)

    async with server:
        print(f'Listening at {HOST}:{PORT}')
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print('Server closing')
