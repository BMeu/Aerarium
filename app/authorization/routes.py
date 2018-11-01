#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The routes of the authorization blueprint.
"""

from flask import flash
from flask import Markup
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import current_user
from flask_login import fresh_login_required
from werkzeug.urls import url_parse

from app import db
from app.authorization import AccountForm
from app.authorization import bp
from app.authorization import EmailForm
from app.authorization import LoginForm
from app.authorization import PasswordResetForm
from app.authorization import User
from app.authorization import logout_required
from app.token import get_validity

# region User Profile


@bp.route('/user', methods=['GET', 'POST'])
@fresh_login_required
def user_profile() -> str:
    """
        Show a page to edit account details. Upon submission, change the account details.

        :return: The HTML response.
    """

    form = AccountForm(obj=current_user, email=current_user.get_email())
    if form.validate_on_submit():

        # Always change the name.
        user = User.load_from_id(current_user.get_id())
        user.name = form.name.data

        # If the user entered a password, change that as well.
        if form.password.data:
            user.set_password(form.password.data)

        # Write the changes to the database.
        db.session.commit()

        # If the email address change send a confirmation mail to the new address.
        if user._email != form.email.data:
            user.send_change_email_address_email(form.email.data)

            validity = get_validity(in_minutes=True)
            flash(Markup(_('An email has been sent to the new address %(email)s. Please open the link included in the \
                            mail within the next %(validity)d minutes to confirm your new email address. Otherwise, \
                            your email address will not be changed.',
                           email='<em>{email}</em>'.format(email=form.email.data), validity=validity)),
                  category='warning')

        flash(_('Your changes have been saved.'))
        return redirect(url_for('authorization.user_profile'))

    return render_template('authorization/account.html', title=_('User Profile'), form=form)


@bp.route('/user/change-email/<string:token>')
def change_email(token: str) -> str:
    """
        Change the email address of the user given in the token to the new address specified in the token.

        :param token: The change-email JWT.
        :return: The HTML response.
    """
    user, email = User.verify_change_email_address_token(token)
    if user is None or not email:
        flash(_('The token is invalid.'), category='error')
        return redirect(url_for('main.index'))

    changed_email = user.set_email(email)
    if changed_email:
        db.session.commit()
        flash(_('Your email address has successfully been changed.'))
    else:
        flash(_('The email address already is in use.'), category='error')

    return redirect(url_for('main.index'))

# endregion

# region Password Reset


@bp.route('/reset-password', methods=['GET', 'POST'])
@logout_required
def reset_password_request() -> str:
    """
        Show a form to request resetting the password and process it upon submission.

        :return: The HTML response.
    """

    validity = get_validity(in_minutes=True)
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
@logout_required
def reset_password(token: str) -> str:
    """
        Show a form to reset the password.

        :param token: The token the user has been sent confirming that the password reset is valid.
        :return: The HTML response.
    """

    user = User.verify_password_reset_token(token)
    if user is None:
        flash(_('The token is invalid.'), category='error')
        return redirect(url_for('main.index'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash(_('Your password has successfully been changed.'))
        return redirect(url_for('authorization.login'))

    return render_template('authorization/reset_password.html', title=_('Reset Your Password'), form=form)

# endregion

# region Login/Logout


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

# endregion
