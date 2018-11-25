#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for users and authorizations.
"""

from flask import Blueprint

from app.views.authorization.user import AccountForm
from app.views.authorization.user import DeleteAccountForm
from app.views.authorization.user import EmailForm
from app.views.authorization.user import LoginForm
from app.views.authorization.user import logout_required
from app.views.authorization.user import PasswordResetForm
from app.views.authorization.user import User

bp = Blueprint('authorization', __name__)

__all__ = [
            'AccountForm',
            'bp',
            'DeleteAccountForm',
            'EmailForm',
            'LoginForm',
            'logout_required',
            'PasswordResetForm',
            'User'
          ]

# noinspection PyPep8
from app.views.authorization import routes  # noqa: E402,F401
