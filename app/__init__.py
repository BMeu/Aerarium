# -*- coding: utf-8 -*-

"""
    The main module containing all functionality.
"""

from app.request import register_after_request_handlers
from app.request import register_before_request_handlers
from app.application import babel
from app.application import bcrypt
from app.application import create_app
from app.application import csrf
from app.application import db
from app.application import get_app
from app.application import login
from app.application import mail
from app.application import migrate
from app.converters import timedelta_to_minutes
from app.email import Email
from app.pagination import Pagination

__all__ = [
    'babel',
    'bcrypt',
    'create_app',
    'csrf',
    'db',
    'Email',
    'get_app',
    'login',
    'mail',
    'migrate',
    'Pagination',
    'register_after_request_handlers',
    'register_before_request_handlers',
    'timedelta_to_minutes',
]
