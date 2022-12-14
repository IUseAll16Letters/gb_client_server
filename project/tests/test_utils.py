import re
import unittest

from project.utils.utils import *
from project.utils import config


def remove_time_from_byteobject(message: bytes):
    message = message.decode(config.ENCODING)
    pattern = re.compile(r', "time": \d*\.\d*')
    return pattern.sub('', message).encode(config.ENCODING)


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.user_data = {'user': {'username': 'u2', 'password': 'password'}}
        self.get_database_object = get_database_object('./test_db.txt')
        self.username = get_user_data_from_set(self.user_data)
        self.authorized = {'u2': 'StreamWriter', 'user1': 'StreamWriter'}

    def test_make_correct_authenticate_message(self):
        result_message = remove_time_from_byteobject(make_message(config.Message.authenticate, **{'username': 'Herasimu'}))
        required_message = b'{"action": 1, "username": "Herasimu"}'
        self.assertEqual(result_message, required_message, msg=f'Wrong message for authenticate test')

    def test_make_correct_msg_message(self):
        result_message = remove_time_from_byteobject(make_message(
            config.Message.msg,
            **{'from': 'Herasimu', 'to': 'Santa-Claus', 'message': "Hello santa!"}))
        required_message = b'{"action": 3, "from": "Herasimu", "message": "Hello santa!", "to": "Santa-Claus"}'
        self.assertEqual(result_message, required_message, msg='Wrong message for msg test')

    def test_make_correct_quit_message(self):
        result_message = remove_time_from_byteobject(make_message(
            config.Message.quit,
        ))
        required_message = b'{"action": 9}'
        self.assertEqual(result_message, required_message, msg='wrong quit message')

    def test_password_hashing_is_correct(self):
        self.assertEqual(
            make_secure_password('password'),
            'CCADBC1A760A45EAD104A72A7618E81C7C4F74E6AF336E7F38434519EF0D211A',
            msg='The passwords should be equal'
        )

    def test_get_database_objects_return_dict(self):
        self.assertIsInstance(self.get_database_object, dict,
                              msg=f'Get db object returns wrong class {self.get_database_object.__class__}')

    def test_correct_userdata_from_set(self):
        user_data = get_user_data_from_set({'user': {'username': 'user1', 'password': 'password1'}})
        self.assertEqual(user_data, ('user1', 'password1'), msg=f'Wrong userdata taken from get_user_data_from_set')

    def test_get_userdata_raises_key_error_at_wrong_dict(self):
        with self.assertRaises(KeyError):
            get_user_data_from_set({'user': {'ONE': 'TWO', 'THREE': 'password1'}})

    def test_user_is_authorized(self):
        is_authorized_flag = is_authorized(self.user_data, self.authorized)
        self.assertTrue(is_authorized_flag, msg=f'Wrong result for {self.username}\n'
                                                f'{self.authorized = }')