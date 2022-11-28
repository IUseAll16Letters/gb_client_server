import asyncio
import re
import unittest

from project.utils.utils import *
from project.utils.config import *


def remove_ping_timings_from_list(list_of_strings: list) -> list:
    re_pattern = re.compile(r' \| ping: -?\d*.\d* s')
    return list(map(lambda x: re_pattern.sub('', x), list_of_strings))


class TestServerMessageHandler(unittest.TestCase):

    def test_server_handler(self):

        response_results = []

        async def _tcp_client():
            nonlocal response_results
            try:
                reader, writer = await asyncio.open_connection(host=HOST, port=PORT)
                print(reader, writer)

            except ConnectionRefusedError:
                print('Remote server is not responding')

            messages = [
                (Message.authenticate, {'user': {'username': 'u2', 'password': 'password'}}),
                (Message.ping, dict()),
                (Message.presence, dict()),
                (Message.coffee, dict()),
            ]

            for message in messages:
                writer.write(make_message(message[0], **message[1]))
                await writer.drain()

                server_response = await reader.read(PACKAGE_SIZE)
                _, message = handle_response(server_response)
                print(f'{message = }')
                response_results.append(message)

            writer.close()

        async def connect_server_main():
            await asyncio.gather(asyncio.create_task(_tcp_client()))

        asyncio.run(connect_server_main())

        required_results = [
            'response: 200 | message: Authorized',
            'response: 200 | ping: -0.49531 s',
            'response: 200',
            'response: 418 | message: Server is a teapot'
        ]
        required_results = remove_ping_timings_from_list(required_results)
        response_results = remove_ping_timings_from_list(response_results)
        self.assertEqual(response_results, required_results, msg='Wrong response from server')
