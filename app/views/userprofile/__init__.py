#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for users and authorizations.
"""

from flask import Blueprint

bp = Blueprint('userprofile', __name__)

# noinspection PyPep8
from app.views.userprofile import routes  # noqa: E402,F401
