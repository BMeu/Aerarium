#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for managing roles.
"""

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import gettext as _
from flask_login import login_required

from app import db
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import RolePagination
from app.userprofile import User
from app.userprofile import UserPagination
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
    role_query = Role.get_search_query(search_term=search_form.search_term)

    # Get the pagination object.
    page = request.args.get('page', 1, type=int)
    pagination = RolePagination(role_query.order_by(Role.name), page)

    title = _('Roles')
    return render_template('administration/roles.html', title=title, pagination=pagination, search_form=search_form)


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
    header_form = RoleHeaderDataForm(obj=role)
    if header_form.validate_on_submit():
        header_form.populate_obj(role)
        db.session.commit()

        flash(_('The role has been updated.'))
        return redirect(url_for('.role_edit', name=role.name))

    return render_template('administration/role_header.html', role=name, header_form=header_form)


@bp.route('/role/<string:name>/permissions', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EditRole)
def role_permissions(name: str) -> str:
    """
        Show a form to a role's permissions.

        :param name: The name of the role.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    return render_template('administration/role_permissions.html', role=name)


@bp.route('/role/<string:name>/users')
@login_required
@permission_required(Permission.EditRole)
def role_users(name: str) -> str:
    """
        List all users to whom the given role is assigned.

        :param name: The name of the role.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    # Get a search term and the resulting query. If no search term is given, all users will be returned.
    search_form = SearchForm()
    user_query = User.get_search_query(query=role.users, search_term=search_form.search_term)

    # Get the pagination object.
    page = request.args.get('page', 1, type=int)
    # noinspection PyProtectedMember
    pagination = UserPagination(user_query.order_by(User.name, User._email), page)

    return render_template('administration/role_users.html', role=name, pagination=pagination, search_form=search_form)


@bp.route('/role/<string:name>/delete', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EditRole)
def role_delete(name: str) -> str:
    """
        Show a form to delete the given role and process that form.

        :param name: The name of the role.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    # TODO: Disable deleting if this is the last role.
    # TODO: Disable deleting if this is the last role with permissions to edit roles.
    # Create (and possibly process) the delete form.
    delete_form = RoleDeleteForm(role)
    if delete_form.validate_on_submit():
        try:
            new_role_id = delete_form.new_role.data
            new_role = Role.load_from_id(new_role_id)
        except AttributeError:
            # The new_role field might not exist because there are no users.
            new_role = None

        role.delete(new_role)

        flash(_('The role has been deleted.'))
        return redirect(url_for('.roles_list'))

    return render_template('administration/role_delete.html', role=name, delete_form=delete_form)
