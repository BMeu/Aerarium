# -*- coding: utf-8 -*-

"""
    Functions creating logging handlers.
"""

from typing import List

from logging import Formatter
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from sys import stdout

from app.logging import SecureSMTPHandler


def create_file_handler(level: int, formatter: Formatter, file: str, max_file_size: int, max_num_of_files: int)\
        -> RotatingFileHandler:
    """
        Initialize a rotating file handler that will insert all events into the specified file.

        The path of `file` must exist.

        :param level: The minimum logging level, e.g. :attr    :`logging.INFO` or :attr:`logging.ERROR`.
        :param formatter: The logging formatter that is applied to the each log record.
        :param file: The path and name of the file to which log records will be written.
        :param max_file_size: The maximum file size in KiB of each file.
        :param max_num_of_files: The maximum number of log files.
        :return: The initialized rotating file handler.
    """

    handler = RotatingFileHandler(file, maxBytes=max_file_size * 1024, backupCount=max_num_of_files)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler


def create_mail_handler(level: int, formatter: Formatter, sender: str, recipients: List[str], subject: str, server: str,
                        port: int = 25, user: str = None, password: str = None, tls: bool = False, ssl: bool = False) \
        -> SecureSMTPHandler:
    """
        Initialize a logging handler that will send all events via mail.

        :param level: The minimum logging level, e.g. :attr:`logging.INFO` or :attr:`logging.ERROR`.
        :param formatter: The logging formatter that is applied to the each log record.
        :param sender: The email address of the sender.
        :param recipients: List of email address to which logs will be sent.
        :param subject: The subject of each log mail.
        :param server: The name of the SMTP server.
        :param port: The port under which the server is reachable (defaults to `25`).
        :param user: The username for authentication against the server (defaults to `None`).
        :param password: The corresponding password (defaults to `None`).
        :param tls: Whether to connect to the server via TLS (defaults to `False`).
        :param ssl: Whether to connect to the server via SSL (defaults to `False`).
        :return: The initialized SMTP handler.
    """

    # Set some options.
    credentials = (user, password) if user and password else None
    secure = () if tls else None
    host = (server, port)

    handler = SecureSMTPHandler(host, sender, recipients, subject, credentials, secure, ssl)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler


def create_stream_handler(level: int, formatter: Formatter) -> StreamHandler:
    """
        Initialize a logging handler that will print all events to ``STDOUT``.

        :param level: The minimum logging level, e.g. :attr:`logging.INFO` or :attr:`logging.ERROR`.
        :param formatter: The logging formatter that is applied to the each log record.
        :return: The initialized stream handler.
    """

    handler = StreamHandler(stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler
