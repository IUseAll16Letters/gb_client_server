if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import time

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncConnection

from asyncio.streams import StreamWriter, StreamReader
from project.utils.config import *
from project.utils.utils import handle_request, parse_start_arguments
from project.utils.db_utils import setup_db
from project import logs


authorized = dict()


async def main() -> None:

    async def handler(reader: StreamReader, writer: StreamWriter) -> None:
        """
        Main server handler. Process requests from users with handle_request() function.
        """

        logs.ServerLoggerObject.logger.info(
            msg=f'Connection from {writer.get_extra_info("peername")} | waiting authorize')
        username = None
        try:
            while True:
                # TODO: If there are more than one message in buffer?
                #  for msg in request.replace(b'}{, b'}&|&{').split(b'&|&')
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

        except ConnectionResetError:
            if username:
                logs.ServerLoggerObject.logger.info(msg=f'User "{username}" disconnected')
                try:
                    authorized.pop(username)
                except KeyError:
                    logs.ServerLoggerObject.logger.error(
                        msg=f'Server error | {username} {writer.get_extra_info("peername")} has already left')

            else:
                logs.ServerLoggerObject.logger.info(
                    msg=f"{writer.get_extra_info('peername')} has disconnected without authorization"
                )
        writer.close()

    arguments = parse_start_arguments()
    engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}")

    # TODO: Как правильно передавать объект подключения к бд??
    async with engine.connect() as conn:
        conn: AsyncConnection
        await setup_db(conn)
        server = await asyncio.start_server(client_connected_cb=handler, host=arguments.addr, port=arguments.port)

        async with server:
            logs.ServerLoggerObject.logger.debug(msg=f'Listening at {arguments.addr}:{arguments.port}')
            print(f'Listening at {arguments.addr}:{arguments.port}')
            await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logs.ServerLoggerObject.logger.warning(msg='Server closing')
