#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for the user settings pages.
"""

from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_babel import refresh
from flask_login import current_user
from flask_login import login_required

from app import db
from app.views.userprofile import bp
from app.views.userprofile.forms import UserSettingsForm


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings() -> str:
    """
        Show a page to edit a user's settings. Upon submission, change the account details.

        :return: The HTML response.
    """

    settings = current_user.settings
    form = UserSettingsForm(obj=settings)
    if form.validate_on_submit():

        # Get the data from the form and save it.
        settings.language = form.language.data
        db.session.commit()

        # Refresh the language to reflect possible changes to the user's language.
        refresh()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('.user_settings'))

    return render_template('userprofile/user_settings.html', title=_('Settings'), form=form)
