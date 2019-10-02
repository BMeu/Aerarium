#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for managing roles.
"""

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask_babel import gettext as _
from flask_login import login_required

from app import db
from app.typing import ResponseType
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import RolePagination
from app.userprofile import User
from app.userprofile import UserPagination
from app.userprofile.decorators import permission_required
from app.views.administration import bp
from app.views.administration.forms import create_permission_form
from app.views.administration.forms import PermissionForm
from app.views.administration.forms import RoleDeleteForm
from app.views.administration.forms import RoleHeaderDataForm
from app.views.administration.forms import RoleNewForm
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
    # noinspection PyProtectedMember
    pagination = RolePagination(role_query.order_by(Role._name))

    title = _('Roles')
    return render_template('administration/roles.html', title=title, pagination=pagination, search_form=search_form)


@bp.route('/role/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EditRole)
def role_new() -> ResponseType:
    """
        Show and process a form to create a new role.

        :return: The HTML response.
    """

    new_role_form = create_permission_form(RoleNewForm, Permission(0))
    if new_role_form.validate_on_submit():
        role = Role(name=new_role_form.name.data)
        role.permissions = new_role_form.permissions
        db.session.add(role)
        db.session.commit()

        flash(_('The new role has been created.'))
        return redirect(url_for('.roles_list'))

    return render_template('administration/role_new.html', new_role_form=new_role_form)


@bp.route('/role/<string:name>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EditRole)
def role_edit(name: str) -> ResponseType:
    """
        Show and process a form to edit an existing role.

        :param name: The name of the role.
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
def role_permissions(name: str) -> ResponseType:
    """
        Show and process a form to change a role's permissions.

        :param name: The name of the role.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    disabled_permissions = None
    if role.is_only_role_allowed_to_edit_roles():
        disabled_permissions = Permission.EditRole

    permission_form = create_permission_form(PermissionForm, role.permissions,
                                             disabled_permissions=disabled_permissions)
    if permission_form.validate_on_submit():
        role.permissions = permission_form.permissions
        db.session.commit()

        flash(_('The role\'s permissions have been updated.'))
        return redirect(url_for('.role_permissions', name=role.name))

    return render_template('administration/role_permissions.html', role=name, permission_form=permission_form)


@bp.route('/role/<string:name>/users')
@login_required
@permission_required(Permission.EditRole)
def role_users(name: str) -> str:
    """
        Show a list of all users to whom the given role is assigned.

        :param name: The name of the role.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    # Get a search term and the resulting query. If no search term is given, all users will be returned.
    search_form = SearchForm()
    user_query = User.get_search_query(query=role.users, search_term=search_form.search_term)

    # noinspection PyProtectedMember
    pagination = UserPagination(user_query.order_by(User.name, User._email))

    return render_template('administration/role_users.html', role=name, pagination=pagination, search_form=search_form)


@bp.route('/role/<string:name>/delete', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EditRole)
def role_delete(name: str) -> ResponseType:
    """
        Show and process a form to delete the given role.

        :param name: The name of the role.
        :return: The HTML response.
    """
    role = Role.load_from_name(name)
    if role is None:
        abort(404)

    # If this is the last role allowed to edit roles show an info text.
    if role.is_only_role_allowed_to_edit_roles():
        deletion_not_possible_text = _('This role cannot be deleted because it is the only one that can edit roles.')
        return render_template('administration/role_delete.html', role=name,
                               deletion_not_possible_text=deletion_not_possible_text)

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
