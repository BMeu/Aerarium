#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The main module containing all functionality.
"""

from app.request import register_after_request_handlers
from app.application import babel
from app.application import create_app
from app.application import db
from app.application import login
from app.application import mail
from app.application import migrate

__all__ = ['babel', 'create_app', 'db', 'login', 'mail', 'migrate', 'register_after_request_handlers']
