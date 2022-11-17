import asyncio

from asyncio.streams import StreamWriter, StreamReader
from utils.config import *
from utils.utils import make_message, handle_message, is_authorized


async def handler(reader: StreamReader, writer: StreamWriter):
    # initializing user
    print(f'User {writer.get_extra_info("peername")} connected | init message ...')
    user_data = handle_message(await reader.read(PACKAGE_SIZE), writer)
    print(f'{user_data = }')
    try:
        username = user_data['user']['username']
        # always authorized
        if is_authorized(username, authorized):
            print('User authorized')
            writer.write(make_message(Message.probe))
            await writer.drain()

            user_response_2 = handle_message(await reader.read(PACKAGE_SIZE), writer)

    except KeyError:
        print('no username passed, fault message disconnecting user')
        writer.close()
        return -1

    return -1


async def main():
    server = await asyncio.start_server(
        handler, HOST, PORT)

    async with server:
        print(f'Serving at {HOST}:{PORT}')
        await server.serve_forever()


if __name__ == '__main__':
    authorized = {}
    asyncio.run(main())
