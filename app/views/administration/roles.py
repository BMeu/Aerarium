#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for managing roles.
"""

from typing import Optional

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import login_required

from app import db
from app import get_app
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User
from app.userprofile.decorators import permission_required
from app.views.administration import bp
from app.views.administration.forms import RoleDeleteForm
from app.views.administration.forms import RoleHeaderDataForm
from app.views.forms import SearchForm


@bp.route('/roles')
@login_required
@permission_required(Permission.EditRole)
def roles_list() -> str:
    """
         Show a list of all roles.

         :return: The HTML response.
    """
    # Get a search term and the resulting query. If no search term is given, all roles will by returned.
    search_form = SearchForm()
    search_term = search_form.get_search_term()
    role_query = Role.get_search_query(search_term)

    # Get the pagination object.
    page = request.args.get('page', 1, type=int)
    application = get_app()
    roles_per_page = application.config['ITEMS_PER_PAGE']
    roles = role_query.order_by(Role.name).paginate(page, roles_per_page, error_out=True)

    roles_on_previous_pages = (page - 1) * roles_per_page
    first_role_on_page = roles_on_previous_pages + 1
    roles_on_page = len(roles.items)

    display_text = _get_role_list_display_text(roles_on_page, first_role_on_page, roles.total, search_term)

    return render_template('administration/roles.html', title=_('Roles'), roles=roles.items, display_text=display_text,
                           total_pages=roles.pages, current_page=roles.page,
                           search_form=search_form, search_term=search_term
                           )


@bp.route('/role/<string:name>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EditRole)
def role_edit(name: str) -> str:
    """
        Show a form to edit an existing role.

        :param name: The name of the role to edit.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    # Create (and possibly process) the header data form.
    header_form = RoleHeaderDataForm(obj=role, prefix='header_')
    if header_form.submit.data and header_form.validate_on_submit():
        header_form.populate_obj(role)
        db.session.commit()

        flash(_('The role has been updated.'))
        return redirect(url_for('.role_edit', name=role.name))

    # List all users to whom this role is assigned.
    # TODO: Add pagination to the user list.
    users = role.users.order_by(User.name).all()

    # TODO: Disable deleting if this is the last role.
    # TODO: Disable deleting if this is the last role with permissions to edit roles.
    # Create (and possibly process) the delete form.
    delete_form = RoleDeleteForm(role, prefix='delete_')
    if delete_form.submit.data and delete_form.validate_on_submit():
        try:
            new_role_id = delete_form.new_role.data
            new_role = Role.load_from_id(new_role_id)
        except AttributeError:
            # The new_role field might not exist because there are no users.
            new_role = None

        role.delete(new_role)

        flash(_('The role has been deleted.'))
        return redirect(url_for('.roles_list'))

    title = _('Edit Role “%(role)s”', role=name)
    return render_template('administration/role_edit.html', title=title, has_tabs=True, role=name,
                           delete_form=delete_form, header_form=header_form, users=users
                           )


def _get_role_list_display_text(roles_on_page: int, first_role_no: int, total_roles: int,
                                search_term: Optional[str] = None) -> str:
    """
        Get a text explaining how many roles are being displayed.

        :param roles_on_page: The number of roles on the current page.
        :param first_role_no: The index of the first role on the page.
        :param total_roles: The total number of roles across all pages (if a search term is given, this is the total
                            number of roles across all pages matching the search term).
        :param search_term: Optionally, the term for which the user searched.
        :return: A localized text displaying the number of roles on the current page.
    """

    last_role_no = first_role_no + roles_on_page - 1

    # Text with a search.
    if search_term:

        # More than one role on the page.
        if roles_on_page >= 2:
            return _('Displaying roles %(first_role_on_page)d to %(last_role_on_page)d of %(total_roles)d matching '
                     '“%(search)s”',
                     first_role_on_page=first_role_no, last_role_on_page=last_role_no, total_roles=total_roles,
                     search=search_term)

        # One role on the page.
        if roles_on_page == 1:
            return _('Displaying role %(role_on_page)d of %(total_roles)d matching “%(search)s”',
                     role_on_page=first_role_no, last_role_on_page=last_role_no, total_roles=total_roles,
                     search=search_term)

        # No roles.
        return _('No roles found matching “%(search)s”', search=search_term)

    # Text without a search.

    # More than one role on the page.
    if roles_on_page >= 2:
        return _('Displaying roles %(first_role_on_page)d to %(last_role_on_page)d of %(total_roles)d',
                 first_role_on_page=first_role_no, last_role_on_page=last_role_no, total_roles=total_roles)

    # One role on the page.
    if roles_on_page == 1:
        return _('Displaying role %(role_on_page)d of %(total_roles)d',
                 role_on_page=first_role_no, total_roles=total_roles)

    # No roles.
    return _('No roles')
