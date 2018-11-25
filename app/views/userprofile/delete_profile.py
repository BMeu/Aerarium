#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for deleting a user's profile.
"""

from flask import abort
from flask import flash
from flask import redirect
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import current_user
from flask_login import fresh_login_required
from jwt import PyJWTError

from app.exceptions import InvalidJWTokenPayloadError
from app.userprofile import User
from app.views.userprofile import bp
from app.views.userprofile.forms import DeleteUserProfileForm


@bp.route('/delete', methods=['POST'])
@fresh_login_required
def delete_profile_request() -> str:
    """
        Send an email to the user to confirm the account deletion request.

        :return: The HTML response.
    """
    form = DeleteUserProfileForm()
    if form.validate_on_submit():
        token = current_user.send_delete_account_email()

        validity = token.get_validity(in_minutes=True)
        flash(_('An email has been sent to your email address. Please open the link included in the mail within the \
                 next %(validity)d minutes to delete your user profile. Otherwise, your user profile will not be \
                 deleted.',
                validity=validity),
              category='warning')

    return redirect(url_for('userprofile.user_profile'))


@bp.route('/delete/<string:token>', methods=['GET'])
@fresh_login_required
def delete_profile(token: str) -> str:
    """
        Delete account of the user given in the token.

        :return: The HTML response.
    """
    try:
        user = User.verify_delete_account_token(token)
    except (InvalidJWTokenPayloadError, PyJWTError):
        return abort(404)

    user.delete()
    flash(_('Your user profile and all data linked to it have been deleted. We would be happy to see you again in the \
             future!'))

    return redirect(url_for('main.index'))