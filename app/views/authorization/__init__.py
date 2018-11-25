#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for users and authorizations.
"""

from flask import Blueprint

from app.views.authorization.user import logout_required
from app.views.authorization.user import User

bp = Blueprint('authorization', __name__)

__all__ = [
            'bp',
            'logout_required',
            'User'
          ]

# noinspection PyPep8
from app.views.authorization import routes  # noqa: E402,F401
