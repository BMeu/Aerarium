# -*- coding: utf-8 -*-

"""
    Routes for the user settings pages.
"""

from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask_babel import gettext as _
from flask_babel import refresh
from flask_login import current_user
from flask_login import login_required

from app import db
from app.typing import ResponseType
from app.views.userprofile import bp
from app.views.userprofile.forms import UserSettingsForm
from app.views.userprofile.forms import UserSettingsResetForm


@bp.route('/settings', methods=['GET', 'POST'])
@login_required  # type: ignore
def user_settings() -> ResponseType:
    """
        Show and process a form to edit a user's settings.

        :return: The HTML response.
    """

    settings = current_user.settings
    settings_form = UserSettingsForm(obj=settings)
    if settings_form.validate_on_submit():

        # Get the data from the form and save it.
        settings.language = settings_form.language.data
        db.session.commit()

        # Refresh the language to reflect possible changes to the user's language.
        refresh()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('.user_settings'))

    reset_form = UserSettingsResetForm()
    return render_template('userprofile/user_settings.html', title=_('Settings'), settings_form=settings_form,
                           reset_form=reset_form)


@bp.route('/settings/reset', methods=['POST'])
@login_required  # type: ignore
def user_settings_reset() -> ResponseType:
    """
        Reset the user settings and redirect to the settings page.

        :return: The HTML response.
    """

    settings = current_user.settings
    reset_form = UserSettingsResetForm()
    if reset_form.validate_on_submit():

        # Reset and save.
        settings.reset()
        db.session.commit()

        # Refresh the language in case it changed.
        refresh()

        flash(_('The settings have been set to their default values.'))

    return redirect(url_for('.user_settings'))
