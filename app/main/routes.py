#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The main blueprint's routes.
"""

from typing import Optional

from flask import flash
from flask import render_template
# noinspection PyProtectedMember
from flask_babel import _

from app.main import bp


@bp.route('/')
@bp.route('/<name>')
def index(name: Optional[str] = None) -> str:
    """
        Show the dashboard, and optionally, greet the user.

        :param name: Name of the user to greet.
        :return: The HTML response.
    """

    if name is not None:
        flash(_('Welcome, %(name)s!', name=name))

    return render_template('dashboard.html', title=_('Dashboard'))
