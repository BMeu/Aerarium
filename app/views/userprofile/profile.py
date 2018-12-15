#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for the user's actual profile.
"""

from flask import abort
from flask import flash
from flask import Markup
from flask import redirect
from flask import render_template
from flask import url_for
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import fresh_login_required
from jwt import PyJWTError

from app import db
from app.exceptions import InvalidJWTokenPayloadError
from app.userprofile import User
from app.views.userprofile import bp
from app.views.userprofile.forms import DeleteUserProfileForm
from app.views.userprofile.forms import UserProfileForm


@bp.route('/profile', methods=['GET', 'POST'])
@fresh_login_required
def user_profile() -> str:
    """
        Show and process a form to edit account details.

        :return: The HTML response.
    """

    profile_form = UserProfileForm(obj=current_user, email=current_user.get_email())
    if profile_form.validate_on_submit():

        # Always change the name.
        user = User.load_from_id(current_user.get_id())
        user.name = profile_form.name.data

        # If the user entered a password, change that as well.
        if profile_form.password.data:
            user.set_password(profile_form.password.data)

        # Write the changes to the database.
        db.session.commit()

        # If the email address changed send a confirmation mail to the new address.
        if user.get_email() != profile_form.email.data:
            token = user.send_change_email_address_email(profile_form.email.data)

            validity = token.get_validity(in_minutes=True)
            flash(Markup(_('An email has been sent to the new address %(email)s. Please open the link included in the \
                            mail within the next %(validity)d minutes to confirm your new email address. Otherwise, \
                            your email address will not be changed.',
                           email='<em>{email}</em>'.format(email=profile_form.email.data), validity=validity)),
                  category='warning')

        flash(_('Your changes have been saved.'))
        return redirect(url_for('userprofile.user_profile'))

    delete_form = DeleteUserProfileForm()
    return render_template('userprofile/profile.html', title=_('User Profile'), profile_form=profile_form,
                           delete_form=delete_form)


@bp.route('/change-email-address/<string:token>')
def change_email(token: str) -> str:
    """
        Change the email address of the user given in the token to the new address specified in the token. Then redirect
        to the home page.

        :param token: The change-email token.
        :return: The HTML response.
    """
    try:
        user, email = User.verify_change_email_address_token(token)
    except (InvalidJWTokenPayloadError, PyJWTError):
        return abort(404)

    changed_email = user.set_email(email)
    if changed_email:
        db.session.commit()
        flash(_('Your email address has successfully been changed.'))
    else:
        flash(_('The email address already is in use.'), category='error')

    return redirect(url_for('main.index'))

# endregion
