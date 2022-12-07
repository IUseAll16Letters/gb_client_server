if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import argparse
import time

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncConnection

from asyncio.streams import StreamWriter, StreamReader
from project.utils.config import *
from project.utils.utils import handle_request, get_database_object, setup_db
from project import logs


authorized = dict()


async def main() -> None:
    argument_parser = argparse.ArgumentParser(description='Server start parameters')
    argument_parser\
        .add_argument('-a', '--addr', type=str, dest='addr', help=f'Server ip, def = {HOST}', default=HOST)
    argument_parser.add_argument('-p', '--port', type=int, dest='port', default=PORT)

    arguments = argument_parser.parse_args()

    engine = create_async_engine("sqlite+aiosqlite:///./users.db")

    async def handler(reader: StreamReader, writer: StreamWriter) -> None:

        logs.ServerLoggerObject.logger.info(
            msg=f'Connection from {writer.get_extra_info("peername")} | waiting authorize')
        username = None
        try:
            while True:
                print(f'SERVER {username = }')
                request = await reader.read(PACKAGE_SIZE)
                resp_data = await handle_request(
                    message=request,
                    writer=writer,
                    authorized=authorized,
                    db_object=conn,
                    user=username
                )
                username = resp_data if resp_data else username
                time.sleep(0.25)

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

    # TODO: Как правильно передавать объект подключения к бд??
    async with engine.connect() as conn:
        conn: AsyncConnection
        await setup_db(conn)
        server = await asyncio.start_server(client_connected_cb=handler, host=arguments.addr, port=arguments.port)

        async with server:
            logs.ServerLoggerObject.logger.info(msg=f'Listening at {HOST}:{PORT}')
            print(f'Listening at {HOST}:{PORT}')
            await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logs.ServerLoggerObject.logger.warning(msg='Server closing')
