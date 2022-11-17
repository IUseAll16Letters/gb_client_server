import asyncio

from utils.config import *
from utils.utils import make_message


async def tcp_client(host: str, port: int):
    reader, writer = await asyncio.open_connection(host=host, port=port)
    user = {
        'user': {
            'username': 'ch1ck3n',
            'status': 'Hello Server',
        }
    }

    while True:
        try:

            writer.write(make_message(Message.presence, **user))
            await writer.drain()

            data = await reader.read(PACKAGE_SIZE)
            print(f'Received: {data}')

            await asyncio.sleep(15)

            writer.write(make_message(Message.quit, **user))
            data = await reader.read(PACKAGE_SIZE)
            print(f'Received closing data: {data}')

            raise KeyboardInterrupt

        except KeyboardInterrupt:
            await writer.drain()
            writer.close()
            break

    print('Connection closed <<')


asyncio.run(tcp_client(HOST, PORT))
