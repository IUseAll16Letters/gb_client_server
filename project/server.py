import asyncio
import argparse
import time

from asyncio.streams import StreamWriter, StreamReader
from project.utils.config import *
from project.utils.utils import handle_request, get_database_object
from project import logs


# Заглушка пока отсутствует базаданных, для сессий
authorized = dict()
database_users = get_database_object(DIR_PATH / 'db.txt')


async def handler(reader: StreamReader, writer: StreamWriter):
    logs.ServerLoggerObject.logger.info(msg=f'Connection from {writer.get_extra_info("peername")} | waiting authorize')
    username = None
    try:
        while True:
            request = await reader.read(PACKAGE_SIZE)
            resp_data = await handle_request(
                message=request,
                writer=writer,
                authorized=authorized,
                db_object=database_users
            )
            # Зачем это тут на каждом сообщении, м? 22.11.28 Это всё еще тут. Надо опимизировать
            if isinstance(resp_data, dict) and resp_data.get('user') is not None:
                username = resp_data.get('user')

            time.sleep(0.5)

    except ConnectionResetError as e:
        if username:
            logs.ServerLoggerObject.logger.info(msg=f'User "{username}" disconnected')
            try:
                authorized.pop(username)
            except KeyError as k_e:
                logs.ServerLoggerObject.logger.error(
                    msg=f'Server error | {username} {writer.get_extra_info("peername")} has already left')

        else:
            logs.ServerLoggerObject.logger.info(
                msg=f"{writer.get_extra_info('peername')} has disconnected without authorization"
            )

    writer.close()


async def main() -> None:
    argument_parser = argparse.ArgumentParser(description='Server start parameters')
    argument_parser.add_argument('-a', '--addr', type=str, dest='addr',
                                 help=f'Server ip, def = {HOST}', default=HOST)
    argument_parser.add_argument('-p', '--port', type=int, dest='port', default=PORT)

    arguments = argument_parser.parse_args()

    server = await asyncio.start_server(handler, arguments.addr, arguments.port)

    async with server:
        logs.ServerLoggerObject.logger.info(msg=f'Listening at {HOST}:{PORT}')
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logs.ServerLoggerObject.logger.warning(msg='Server closing')
