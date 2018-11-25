#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Extensions to the logging interface.
"""

from app.logging.handler_factories import create_file_handler
from app.logging.handler_factories import create_mail_handler
from app.logging.handler_factories import create_stream_handler
from app.logging.secure_smtp_handler import SecureSMTPHandler

__all__ = [
            'create_file_handler',
            'create_mail_handler',
            'create_stream_handler',
            'SecureSMTPHandler'
          ]
