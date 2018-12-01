#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The blueprint responsible for the application administration.
"""

from flask import Blueprint

bp = Blueprint('administration', __name__)

# noinspection PyPep8
from app.views.administration import roles  # noqa: E402,F401
