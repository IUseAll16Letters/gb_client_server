import logging
import traceback

from project.logs.server_logger_configs import config_server_logger
from project.logs.loggers_utils import Log


@Log('server')
def magic_tricks(a, b):
    """функция которая функционирует"""
    return str(a) + ' | ' + str(b)


def main():
    magic_tricks(8, 9)
    for i in traceback.format_stack():
        print(i)
        print('*' * 20)
        break


def upper_main():
    main()


if __name__ == '__main__':
    upper_main()
