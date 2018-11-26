#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for resetting a user's password.
"""

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from jwt import PyJWTError

from app import db
from app.exceptions import InvalidJWTokenPayloadError
from app.userprofile import logout_required
from app.userprofile import User
from app.userprofile.tokens import ChangeEmailAddressToken
from app.views.userprofile import bp
from app.views.userprofile.forms import EmailForm
from app.views.userprofile.forms import PasswordResetForm


@bp.route('/reset-password', methods=['GET', 'POST'])
@logout_required
def reset_password_request() -> str:
    """
        Show a form to request resetting the password and process it upon submission.

        :return: The HTML response.
    """

    form = EmailForm()
    if form.validate_on_submit():
        user = User.load_from_email(form.email.data)
        if user is not None:
            token = user.send_password_reset_email()
        else:
            # Create a fake token to get the validity.
            token = ChangeEmailAddressToken()

        validity = token.get_validity(in_minutes=True)

        # Display a success message even if the specified address does not belong to a user account. Otherwise,
        # infiltrators could deduce if an account exists and use this information for attacks.
        flash(_('An email has been sent to the specified address. Please be aware that the included link for resetting \
                the password is only valid for %(validity)d minutes.', validity=validity))
        return redirect(url_for('userprofile.login'))

    return render_template('userprofile/reset_password_request.html', title=_('Forgot Your Password?'), form=form)


@bp.route('/reset-password/<string:token>', methods=['GET', 'POST'])
@logout_required
def reset_password(token: str) -> str:
    """
        Show a form to reset the password.

        :param token: The token the user has been sent confirming that the password reset is valid.
        :return: The HTML response.
    """

    try:
        user = User.verify_password_reset_token(token)
    except (InvalidJWTokenPayloadError, PyJWTError):
        return abort(404)

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash(_('Your password has successfully been changed.'))
        return redirect(url_for('userprofile.login'))

    return render_template('userprofile/reset_password.html', title=_('Reset Your Password'), form=form)
