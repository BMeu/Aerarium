#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for logging a user in and out.
"""

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import current_user
from werkzeug.urls import url_parse

from app.userprofile import logout_required
from app.userprofile import User
from app.views.userprofile import bp
from app.views.userprofile.forms import LoginForm


@bp.route('/login', methods=['GET', 'POST'])
@logout_required
def login() -> str:
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

            # Redirect to the next page if given (and if the next page is a valid URL). Otherwise, redirect to home.
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')

            return redirect(next_page)

        # Login failed. Just show the login form again.
        flash(_('Invalid email address or password.'), 'error')

    return render_template('userprofile/login.html', title=_('Log In'), form=form)


@bp.route('/logout')
def logout() -> str:
    """
        Log out the user and redirect them to the homepage.

        :return: The HTML response.
    """

    if current_user.is_authenticated:
        User.logout()
        flash(_('You were successfully logged out.'))

    return redirect(url_for('main.index'))
