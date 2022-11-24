import asyncio
import re
import unittest

from project.utils.utils import *
from project.utils.config import *
from project.client import tcp_client
from project.server import handler


def remove_time(message: bytes):
    message = message.decode(ENCODING)
    pattern = re.compile(r', "time": \d*\.\d*')
    return pattern.sub('', message).encode(ENCODING)


class TestServerMessageHandler(unittest.TestCase):
    def setUp(self) -> None:
        async def get_writer_object(r, writer):
            return writer

        async def get_writer():
            writer = await asyncio.gather(
                asyncio.start_server(get_writer_object, HOST, PORT))
            return writer

        self.writer = asyncio.run(get_writer())

    def test_server_is_a_teapot(self):
        print('Server is a teapot')
        result_response = generate_response_message(
            Status.IAmATeapot,
            **{'message': 'Hello. I am a teapot'})
        required_response = b'{"response": 418, "message": "Hello. I am a teapot"}'

        self.assertEqual(
            result_response,
            required_response,
            msg=f'{required_response = }\n{result_response = }'
        )

    def test_server_handles_quit_command(self):
        async def server_main():
            server = await asyncio.start_server(
                handler, HOST, PORT)

            async with server:
                print(f'Listening at {HOST}:{PORT}')
                await server.serve_forever()

        asyncio.run(server_main())


# class AsyncTest(unittest.IsolatedAsyncioTestCase):
#
#     async def test_func(self):
#         result = await
#         self.assertEqual()
