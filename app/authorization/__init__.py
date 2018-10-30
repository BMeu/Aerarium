#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for users and authorizations.
"""

from flask import Blueprint

from app.authorization.user import EmailForm
from app.authorization.user import LoginForm
from app.authorization.user import logout_required
from app.authorization.user import PasswordResetForm
from app.authorization.user import User

bp = Blueprint('authorization', __name__)

__all__ = [
            'bp',
            'EmailForm',
            'LoginForm',
            'logout_required',
            'PasswordResetForm',
            'User'
          ]

# noinspection PyPep8
from app.authorization import routes  # noqa: E402,F401
