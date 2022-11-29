__all__ = ['ServerLoggerObject', 'ClientLoggerObject']

import functools
import inspect
import sys
import logging
import logging.handlers as handlers

from typing import Callable
from project.utils import *


class LoggerFactory:
    _instance = None
    if DEBUG:
        _wraps = set()

    def __init__(self, logger_format: str, file_location: str):
        self.logger_format = logger_format
        self.file_location = DIR_PATH / file_location

        self.config()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def config(self):
        if self.__class__ is ServerLogger:
            self.logger_name = 'server'
            file_handler = handlers\
                .TimedRotatingFileHandler(self.file_location, encoding='utf-8', interval=1, when='midnight')
        else:
            self.logger_name = 'client'
            file_handler = logging.FileHandler(self.file_location, mode='a', encoding='utf-8')

        self.logger = logging.getLogger(self.logger_name)

        log_level = SERVER_LOG_LEVEL if self.logger_name == 'server' else CLIENT_LOG_LEVEL
        self.logger.setLevel(log_level)

        fmt = logging.Formatter(self.logger_format)

        file_handler.setFormatter(fmt)
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)

        if DEBUG:
            sh = logging.StreamHandler(stream=sys.stdout)
            sh.setLevel(log_level)
            sh.setFormatter(fmt)
            self.logger.addHandler(sh)

    def __call__(self, function: Callable):
        if DEBUG:
            self._wraps.update({function.__name__})

        @functools.wraps(function)
        def logger_wrapper(*args, **kwargs):
            _, module, line, caller, call_request, _ = inspect.stack()[1]

            self.logger.info(msg=f'fnc: {function.__name__} | args: {args} | kwargs: {kwargs} | '
                                 f'stated in: {module} | Called from function {caller} line {line} | '
                             , stacklevel=2)

            return function(*args, **kwargs)

        return logger_wrapper


class ServerLogger(LoggerFactory):
    def __repr__(self):
        wraps = f'\nwrapping: [{self._wraps}]' if DEBUG else ''
        return f'ServerLogger | format: {self.logger_format} | saved to: {self.file_location}' + wraps


class ClientLogger(LoggerFactory):
    def __repr__(self):
        wraps = f'\nwrapping: [{self._wraps}]' if DEBUG else ''
        return f'ClientLogger | format: {self.logger_format} | saved to: {self.file_location}' + wraps


ClientLoggerObject = ClientLogger(
    logger_format='%(asctime)s | %(levelname)7s | %(name)s | %(message)s',
    file_location='logs/client.log'
)

ServerLoggerObject = ServerLogger(
    logger_format='%(asctime)s | %(levelname)7s | %(name)s | %(message)s',
    file_location='logs/server.log'
)
