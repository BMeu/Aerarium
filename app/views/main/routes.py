#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The main blueprint's routes.
"""

from flask import redirect
from flask import render_template
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import current_user

from app.views.main import bp


@bp.route('/')
def index() -> str:
    """
        Show the dashboard.

        :return: The HTML response.
    """

    # If the user is not yet logged in, direct them to the login form.
    if not current_user.is_authenticated:
        return redirect(url_for('userprofile.login'))

    return render_template('dashboard.html', title=_('Dashboard'))
