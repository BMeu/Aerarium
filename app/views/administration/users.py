# -*- coding: utf-8 -*-

"""
    Routes for managing users.
"""

from flask import render_template
from flask_babel import gettext as _
from flask_login import login_required

from app.typing import ResponseType
from app.userprofile import Permission
from app.userprofile import User
from app.userprofile import UserPagination
from app.userprofile.decorators import permission_required
from app.views.administration import bp
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
