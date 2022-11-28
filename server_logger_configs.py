import sys
import functools
import logging

from logging import handlers
from project.utils.config import *


def config_server_logger(name: str):
    l_name = str(name).split('/')[-1].replace('.py', '')
    logger_object = logging.getLogger(l_name)
    logger_object.setLevel(SERVER_LOG_LEVEL)

    server_fmt = logging.Formatter('%(asctime)s | %(levelname)7s | %(message)15s | %(name)s | %(fnc_name)s | '
                                   'args=%(arguments)s | kwargs=%(kwarguments)s')

    sh = logging.StreamHandler(stream=sys.stdout)

    log_file = handlers\
        .TimedRotatingFileHandler(DIR_PATH / 'logs/server.log', encoding=ENCODING, interval=1, when='midnight')
    print(DIR_PATH / 'logs/server.log')
    
    log_file.setFormatter(server_fmt)
    log_file.setLevel(SERVER_LOG_LEVEL)
    logger_object.addHandler(log_file)

    sh.setFormatter(server_fmt)
    logger_object.addHandler(sh)

    return l_name





# config_server_logger()

# if __name__ == '__main__':
#     logger.info(msg='info message', extra={'fnc_name': f'from file {logger_name}'})
#     logger.debug(msg='debug message', extra={'fnc_name': f'from file {logger_name}'})
#     logger.warning(msg='warning message', extra={'fnc_name': f'from file {logger_name}'})
#     logger.error(msg='error message', extra={'fnc_name': f'from file {logger_name}'})
