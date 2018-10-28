#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for users and authorizations.
"""

from flask import Blueprint

from app.authorization.user import LoginForm
from app.authorization.user import User

bp = Blueprint('authorization', __name__)

__all__ = [
            'bp',
            'LoginForm',
            'User'
          ]

# noinspection PyPep8
from app.authorization import routes  # noqa: E402,F401
