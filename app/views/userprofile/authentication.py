#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for logging a user in and out.
"""

from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required
from flask_login import login_fresh

from app.typing import ResponseType
from app.userprofile import logout_required
from app.userprofile import User
from app.views.tools import get_next_page
from app.views.userprofile import bp
from app.views.userprofile.forms import LoginForm
from app.views.userprofile.forms import LoginRefreshForm


@bp.route('/login', methods=['GET', 'POST'])
@logout_required
def login() -> ResponseType:
    """
        Show a login form to the user. If they submitted the login form, try to log them in and redirect them to the
        homepage.

        :return: The HTML response.
    """

    form = LoginForm()
    if form.validate_on_submit():
        # Try to login the user.
        user = User.login(email=form.email.data, password=form.password.data, remember_me=form.remember_me.data)
        if user:
            # Login succeeded.
            flash(_('Welcome, %(name)s!', name=user.name))

            next_page = get_next_page()
            return redirect(next_page)

        # Login failed. Just show the login form again.
        flash(_('Invalid email address or password.'), 'error')

    return render_template('userprofile/login.html', title=_('Log In'), form=form)


@bp.route('/login/refresh', methods=['GET', 'POST'])
@login_required  # type: ignore
def login_refresh() -> ResponseType:
    """
        Show a form to refresh a user's login after their login has become stale.

        :return: The HTML response.
    """

    if login_fresh():
        return redirect(url_for('main.index'))

    form = LoginRefreshForm()
    if form.validate_on_submit():
        user = User.refresh_login(form.password.data)
        if user:
            # Login refresh succeeded.
            flash(_('Welcome, %(name)s!', name=user.name))

            next_page = get_next_page()
            return redirect(next_page)

        flash(_('Invalid password.'), 'error')

    return render_template('userprofile/login.html', title=_('Confirm Login'), form=form)


@bp.route('/logout')
def logout() -> ResponseType:
    """
        Log the user out and redirect them to the homepage.

        :return: The HTML response.
    """

    if current_user.is_authenticated:
        User.logout()
        flash(_('You were successfully logged out.'))

    return redirect(url_for('main.index'))
