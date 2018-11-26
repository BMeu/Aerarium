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

    form = UserSettingsForm(obj=current_user.settings)
    if form.validate_on_submit():
        form.populate_obj(current_user.settings)
        db.session.commit()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('.user_settings'))

    return render_template('userprofile/user_settings.html', title=_('Settings'), form=form)
