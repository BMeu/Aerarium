#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The application's main blueprint handling basic functionality such as errors.
"""

from flask import Blueprint

bp = Blueprint('main', __name__)

# noinspection PyPep8
from app.main import errors  # noqa: E402,F401
# noinspection PyPep8
from app.main import routes  # noqa: E402,F401
