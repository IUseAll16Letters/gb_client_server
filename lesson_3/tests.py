# TODO: REMOVE THIS FILE IN FOLDER

import asyncio
import re
import unittest

from project.utils.utils import *
from project.utils import config


def remove_time(message: bytes):
    message = message.decode(config.ENCODING)
    pattern = re.compile(r', "time": \d*\.\d*')
    return pattern.sub('', message).encode(config.ENCODING)


class TestServerUtils(unittest.TestCase):
    # def setUp(self) -> None:
    #     def remove_time(message: bytes):
    #
    #     self.remove_time = remove_time

    def test_correct_message(self):
        result_message = remove_time(make_message(config.Message.authenticate, **{'username': 'Herasima'}))
        required_message = b'{"action": 1, "username": "Herasima"}'
        self.assertEqual(
            result_message,
            required_message,
            msg=f'{required_message = }\n{result_message = }')

    def test_password_verification_correct(self):
        print('test verif true')
        self.assertEqual(verify_password(
            username='u2',
            password='password', db_object=get_database('../db.txt')
        ),
            True,
            msg='The password supplied should be detected as correct')

    def test_password_hashing_correct(self):
        print('test password hashing correct')
        self.assertEqual(
            make_secure_password('password'),
            'CCADBC1A760A45EAD104A72A7618E81C7C4F74E6AF336E7F38434519EF0D211A',
            msg='The passwords should be equal'
        )


class TestServerMessageHandler(unittest.TestCase):
    def setUp(self) -> None:
        async def get_writer_object(r, writer):
            return writer

        async def get_writer():
            writer = await asyncio.gather(
                asyncio.start_server(get_writer_object, config.HOST, config.PORT))
            return writer

        writer_ = asyncio.run(get_writer())

        self.writer = writer_

    def tearDown(self) -> None:
        pass

    def test_server_handles_authorize_message(self):
        async def sth():
            await handle_message(b'{"action": 1, "message": "YOU"}',
                                 self.writer,
                                 authorized={'u1': None})

        async def get_result():
            result = await asyncio.gather(asyncio.create_task(sth()))
            return result

        res = asyncio.run(get_result())
        print('result >>> ', res)
        self.assertEqual(res, False, msg='AAAAA')

    def test_server_is_a_teapot(self):
        result_response = generate_response_message(
            Status.IAmATeapot,
            **{'message': 'Hello. I am a teapot'})
        required_response = b'{"response": 418, "message": "Hello. I am a teapot"}'

        self.assertEqual(
            result_response,
            required_response,
            msg=f'{required_response = }\n{result_response = }'
        )


# class TestClientUtils(unittest.TestCase):
#     pass


functions = {
    'make_message',  # server/client
    'generate_response_message',  # server
    'handle_message',  # server
    'handle_response',  # client
    'get_database',  # server
    'initialize',  # server
    'make_secure_password',  # server
    'verify_password',  # server
    'get_user_data_from_set',  # server
    'authorize',  # server
    'is_authorized',  # server
    'client_send_message_loop',  # client
}
