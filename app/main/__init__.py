#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The application's main blueprint handling basic functionality such as users and settings.
"""

from flask import Blueprint

bp = Blueprint('main', __name__)

# noinspection PyPep8
from app.main import routes  # noqa: E402,F401
