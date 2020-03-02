# -*- coding: utf-8 -*-

"""
    Routes for managing users.
"""

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask_babel import gettext as _
from flask_babel import refresh
from flask_login import login_required

from app import db
from app.typing import ResponseType
from app.userprofile import Permission
from app.userprofile import User
from app.userprofile import UserPagination
from app.userprofile.decorators import permission_required
from app.views.administration import bp
from app.views.administration.forms import UserSettingsForm
from app.views.administration.forms import UserSettingsResetForm
from app.views.forms import SearchForm


@bp.route('/users')
@login_required  # type: ignore
@permission_required(Permission.EditUser)
def users_list() -> ResponseType:
    """
        Show a list of all users.

        :return: The response for this view.
    """

    # Get a search term and the resulting query. If no search term is given, all users will be returned.
    search_form = SearchForm()
    user_query = User.get_search_query(search_term=search_form.search_term)
    pagination = UserPagination(user_query.order_by(User.name))

    title = _('Users')
    return render_template('administration/users.html', title=title, pagination=pagination, search_form=search_form)


@bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required  # type: ignore
@permission_required(Permission.EditUser)
def user_edit(user_id: int) -> ResponseType:
    """
        Show and process a form to edit an existing user.

        :param user_id:  The ID of the user.
        :return: The response for this view.
    """

    user = User.load_from_id(user_id)
    if user is None:
        abort(404)

    return render_template('administration/user_header.html', user=user)


@bp.route('/user/<int:user_id>/settings', methods=['GET', 'POST'])
@login_required  # type: ignore
@permission_required(Permission.EditUser)
def user_settings(user_id: int) -> ResponseType:
    """
        Show and process a form to edit a user's settings.

        :param user_id: The ID of the user whose settings will be managed.
        :return: The response for this view.
    """

    user = User.load_from_id(user_id)
    if user is None:
        abort(404)

    settings = user.settings
    settings_form = UserSettingsForm(obj=settings)
    if settings_form.validate_on_submit():

        # Get the data from the form and save it.
        settings.language = settings_form.language.data
        db.session.commit()

        # Refresh the language in case the current user is editing themselves and they have changed their language.
        refresh()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('.user_settings', user_id=user_id))

    reset_form = UserSettingsResetForm()
    return render_template('administration/user_settings.html',
                           user=user,
                           settings_form=settings_form,
                           reset_form=reset_form)


@bp.route('/user/<int:user_id>/settings/reset', methods=['POST'])
@login_required  # type: ignore
@permission_required(Permission.EditUser)
def user_settings_reset(user_id: int) -> ResponseType:
    """
        Reset the user's settings and redirect to the settings page.

        :param user_id: The ID of the user whose settings will be reset.
        :return: The response for this view.
    """

    user = User.load_from_id(user_id)
    if user is None:
        abort(404)

    settings = user.settings
    reset_form = UserSettingsResetForm()
    if reset_form.validate_on_submit():
        settings.reset()
        db.session.commit()

        # Refresh the language in case the current user is editing themselves and they have changed their language.
        refresh()

        flash(_('The settings have been set to their default values.'))

    return redirect(url_for('.user_settings', user_id=user_id))
