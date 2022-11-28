import sys
import functools
import logging

from project.logs.server_logger_configs import config_server_logger


class Log:
    def __init__(self, logger_name):
        config_server_logger(logger_name)
        self.logger = logging.getLogger(logger_name)

    def __call__(self, fnc):
        @functools.wraps(fnc)
        def wrapper(*args, **kwargs):
            try:
                print(f'using logger: {self.logger}')
                result = fnc(*args, **kwargs)
                self.logger.debug(msg=f'Fine result',
                                  extra={'fnc_name': fnc.__name__,
                                                            'arguments': args,
                                                            'kwarguments': kwargs})
                return result
            except Exception as e:
                self.logger.error(msg='UNKNOWN EXCEPTION', extra={'fnc_name': fnc.__name__,
                                                                  'arguments': args,
                                                                  'kwarguments': kwargs})
                print(f'Uncaught exception with message: {e}')

        return wrapper
