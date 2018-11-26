#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for users and authorizations.
"""

from flask import Blueprint

bp = Blueprint('userprofile', __name__)

# noinspection PyPep8
from app.views.userprofile import authentication  # noqa: E402,F401
# noinspection PyPep8
from app.views.userprofile import delete_profile  # noqa: E402,F401
# noinspection PyPep8
from app.views.userprofile import password_reset  # noqa: E402,F401
# noinspection PyPep8
from app.views.userprofile import profile  # noqa: E402,F401
# noinspection PyPep8
from app.views.userprofile import user_settings  # noqa: E402,F401
