#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The routes of the authorization blueprint.
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

from app import db
from app import get_app
from app.authorization import bp
from app.authorization import EmailForm
from app.authorization import LoginForm
from app.authorization import PasswordResetForm
from app.authorization import User


@bp.route('/login', methods=['GET', 'POST'])
def login() -> str:
    """
        Show a login form to the user. If they submitted the login form, try to log them in and redirect them to the
        homepage.

        :return: The HTML response.
    """

    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

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

    return render_template('authorization/login.html', title=_('Log In'), form=form)


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


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request() -> str:
    """
        Show a form to request resetting the password and process it upon submission.

        :return: The HTML response.
    """

    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Get the validity of the token and convert it from seconds to minutes for display.
    application = get_app()
    validity = application.config['TOKEN_VALIDITY'] / 60

    form = EmailForm()
    if form.validate_on_submit():
        user = User.load_from_email(form.email.data)
        if user is not None:
            user.send_password_reset_email()

        # Display a success message even if the specified address does not belong to a user account. Otherwise,
        # infiltrators could deduce if an account exists and use this information for attacks.
        flash(_('An email has been sent to the specified address. Please be aware that the included link for resetting \
                the password is only valid for %(validity)d minutes.', validity=validity))
        return redirect(url_for('authorization.login'))

    return render_template('authorization/reset_password_request.html', title=_('Forgot Your Password?'), form=form,
                           validity=validity, )


@bp.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password(token: str) -> str:
    """
        Show a form to reset the password.

        :param token: The token the user has been sent confirming that the password reset is valid.
        :return: The HTML response.
    """

    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_password_reset_token(token)
    if user is None:
        return redirect(url_for('main.index'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash(_('Your password has successfully been changed.'))
        return redirect(url_for('authorization.login'))

    return render_template('authorization/reset_password.html', title=_('Reset Your Password'), form=form)
