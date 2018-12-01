#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for managing roles.
"""

from flask import render_template
from flask import request
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import login_required

from app import get_app
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile.decorators import permission_required
from app.views.administration import bp


@bp.route('/roles')
@login_required
@permission_required(Permission.EditRole)
def roles_list() -> str:
    """
         Show a list of all roles.

         :return: The HTML response.
    """
    # Get the pagination object.
    page = request.args.get('page', 1, type=int)
    application = get_app()
    roles_per_page = application.config['ITEMS_PER_PAGE']
    roles = Role.query.order_by(Role.name).paginate(page, roles_per_page, error_out=True)

    roles_on_previous_pages = (page - 1) * roles_per_page
    first_role_on_page = roles_on_previous_pages + 1
    last_role_on_page = roles_on_previous_pages + len(roles.items)

    return render_template('administration/roles.html', title=_('Roles'), roles=roles.items, total_roles=roles.total,
                           first_role_on_page=first_role_on_page, last_role_on_page=last_role_on_page,
                           total_pages=roles.pages, current_page=roles.page
                           )
