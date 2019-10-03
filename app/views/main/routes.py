# -*- coding: utf-8 -*-

"""
    The main blueprint's routes.
"""

from flask import redirect
from flask import render_template
from flask import url_for
from flask_babel import gettext as _
from flask_login import current_user

from app.views.main import bp
from app.typing import ResponseType


@bp.route('/')
def index() -> ResponseType:
    """
        Show the dashboard.

        :return: The response for this view.
    """

    # If the user is not yet logged in, direct them to the login form.
    if not current_user.is_authenticated:
        return redirect(url_for('userprofile.login'))

    return render_template('dashboard.html', title=_('Dashboard'))
