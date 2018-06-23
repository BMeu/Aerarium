#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The main blueprint's routes.
"""

from typing import Optional

from flask import current_app
from flask import render_template
# noinspection PyProtectedMember
from flask_babel import _

from app.main import bp


@bp.route('/')
@bp.route('/<name>')
def index(name: Optional[str] = None) -> str:
    """
        Show the homepage, and optionally, greet the user.

        :param name: Name of the user to greet. If not given, a general message will be displayed (defaults to
            ``None``).
        :return: The HTML response.
    """

    if name is not None:
        title = _('Welcome, %(name)s!', name=name)
    else:
        title = _('Welcome to %(title)s!', title=current_app.config['TITLE_SHORT'])

    return render_template('base.html', title=title)
