#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import List
from typing import Optional

from flask_babel import gettext as _
from flask_sqlalchemy import BaseQuery

from app import db
from app import Pagination
from app.exceptions import DeletionPreconditionViolationError
from app.userprofile import Permission

"""
    The application's role model.
"""


class Role(db.Model):
    """
        The class representing a role with certain permissions.
    """

    # region Fields and Properties

    id = db.Column(db.Integer, primary_key=True)
    """
        The role's unique ID.
    """

    _name = db.Column('name', db.String(255), unique=True)
    """
        A name describing the role.
    """

    _permissions = db.Column('permissions', db.BigInteger, default=0)
    """
        An integer representing the permissions the role has. Use :attr:`.permissions` to access the actual enum member.

        Each permission (:class:`.Permission`) has a value that is a power of two. Therefore, the combination of
        permissions can be represented as an integer.
    """

    users = db.relationship('User', backref='role', lazy='dynamic')
    """
        A list of :class:`users` which have this role.
    """

    invalid_names: List[str] = ['new']
    """
        A list of names that may not be used for a role's name.
    """

    @property
    def name(self) -> str:
        """
            Get the role's name.

            :return: The role's unique name.
        """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
            Set the role's name.

            The name may not be one of the strings listed in :attr:`invalid_names`.

            :param value: The role's new name.
            :raise ValueError: if an invalid name is given.
        """
        if value in self.invalid_names:
            raise ValueError('The name may not be one of ' + ', '.join(self.invalid_names))

        # TODO: Check for unique name?

        self._name = value

    # endregion

    # region Initialization

    def __init__(self, name: str) -> None:
        """
            Initialize a role with the given name.

            :param name: The role's name. It must not be one of the strings listed in :attr:`invalid_names`.
            :raise ValueError: if an invalid name is given.
        """
        self.name = name

    @staticmethod
    def load_from_id(role_id: int) -> Optional['Role']:
        """
            Load the role with the given ID from the database.

            :param role_id: The ID of the role to load.
            :return: The loaded role if it exists, `None` otherwise.
        """
        return Role.query.get(role_id)

    @staticmethod
    def load_from_name(name: str) -> Optional['Role']:
        """
            Load the role with the given name from the database.

            :param name: The name of the role load.
            :return: The loaded role if it exists, `None` otherwise.
        """
        return Role.query.filter_by(_name=name).first()

    @staticmethod
    def load_roles_with_permission(permission: Permission) -> List['Role']:
        """
            Get all roles that have the given permission.

            :param permission: The permission that the roles must have.
            :return: A list of roles that have the given permission.
        """

        raw_value = permission.value
        return Role.query.filter(Role._permissions.op('&')(raw_value) == raw_value).all()

    # endregion

    # region Permissions

    @property
    def permissions(self) -> Permission:
        """
            Get the permission (combination) that represents the permissions this role has.

            :return: An enum member of :class:`Permission` representing the role`s permissions.
        """
        # For some reason, PyCharm thinks, self._permissions has type Permission...
        # noinspection PyTypeChecker
        if self._permissions is None or self._permissions < 0:
            return Permission(0)

        # noinspection PyTypeChecker
        return Permission(self._permissions)

    @permissions.setter
    def permissions(self, permission: Permission) -> None:
        """
            Set the given permissions for this role.

            This will overwrite all existing permissions.

            If this role is only one allowed to edit roles, but the new permissions do not include the permission to
            edit roles,

            :param permission: An enum member of :class:`Permission` representing the role`s new permissions (may be a
                          combination of multiple enum members).
        """
        if permission is None:
            permission = Permission(0)

        # If the permission to edit roles is not included in the new permissions, but this is the only role allowed to
        # edit roles, re-add the permission to avoid a situation where no one can edit roles anymore.
        if permission & Permission.EditRole != Permission.EditRole and self.is_only_role_allowed_to_edit_roles():
            permission |= Permission.EditRole

        self._permissions = permission.value

    def has_permission(self, permission: Permission) -> bool:
        """
            Determine if the role has the given permission.

            The role will always have the empty permission `Permission(0)`.

            :param permission: The permission to check for.
            :return: `True` if the role has the requested permission, `False` otherwise.
        """
        return permission & self.permissions == permission

    def has_permissions_all(self, *permissions: Permission) -> bool:
        """
            Determine if the role has all of the given permissions.

            The role will always have the empty permission `Permission(0)`.

            :param permissions: The permissions to check for.
            :return: `True` if the role has all of the requested permissions, `False` otherwise.
        """
        for permission in permissions:
            if permission & self.permissions != permission:
                return False

        return True

    def has_permissions_one_of(self, *permissions: Permission) -> bool:
        """
            Determine if the role has (at least) one of the given permissions.

            The role will always have the empty permission `Permission(0)`. Thus, if the empty permission is part of
            the given permissions, the result will always be `True`.

            :param permissions: The permissions to check for.
            :return: `True` if the role has one of the requested permission, `False` otherwise.
        """
        for permission in permissions:
            if permission & self.permissions == permission:
                return True

        return False

    def is_only_role_allowed_to_edit_roles(self) -> bool:
        """
            Determine if this role is the only one allowed to edit roles.

            :return: `True` if it is the only role, `False` otherwise or if this role does not have the permission to
                     edit roles.
        """
        permission = Permission.EditRole
        if not self.has_permission(permission):
            return False

        roles_with_permissions = Role.load_roles_with_permission(permission)
        if len(roles_with_permissions) == 1 and roles_with_permissions[0] == self:
            return True

        return False

    # endregion

    # region Delete

    def delete(self, new_role: Optional['Role'] = None):
        """
            Delete this role. If there are users to whom this role is assigned, their role will be set to `new_role`.

            The role cannot be deleted if this is the last role that has the permission to edit roles. In this case,

            :param new_role: Required if there are users to whom this role is assigned. Must not be this role.
            :raise DeletionPreconditionViolationError: If this role is the only one with the permission to edit roles.
            :raise ValueError: If there are users to whom this role is assigned and `new_role` is not valid.
        """
        if self.is_only_role_allowed_to_edit_roles():
            raise DeletionPreconditionViolationError('Cannot delete the only role with the permission to edit roles.')

        if self == new_role:
            raise ValueError('The new role must not be the role that will be deleted.')

        has_users = self.users.count() >= 1
        if has_users:
            if new_role is None:
                raise ValueError('A new role must be given that is different to this role if there are users')

            # Assign the new role to all users.
            for user in self.users:
                user.role = new_role

        db.session.delete(self)
        db.session.commit()

    # endregion

    # region DB Queries

    @staticmethod
    def get_search_query(query: Optional[BaseQuery] = None, search_term: Optional[str] = None) -> BaseQuery:
        """
            Get a query that searches the roles for the given search term on their names.

            The search term may contain wildcards (`*`).

            :param query: A base query object. If not given, the `User.query` will be used.
            :param search_term: The name for which the roles will be searched. If `None`, a non-filtering query be
                                returned.
            :return: The query object.
        """
        if query is None:
            query = Role.query

        if search_term is None or search_term == '':
            return query

        # Replace the wildcard character with the SQL wildcard.
        search_term = search_term.replace('*', '%')
        return query.filter(Role._name.like(search_term))

    # endregion

    # region System

    def __repr__(self) -> str:
        """
            Get a string representation of the role.

            :return: A string representation of the role.
        """
        return f'<Role [{self.id}] "{self.name}" [{self.permissions}]>'

    # endregion


class RolePagination(Pagination):
    """
        A pagination object for roles specializing the info texts.
    """

    def get_info_text(self, search_term: Optional[str] = None) -> str:
        """
            Get an informational text explaining how many results are being displayed on the current page.

            :param search_term: If given, this term will be included in the info text to explain that the results are
                                being filtered by this value.
            :return: The info text.
        """

        # Text with a search.
        if search_term:

            # More than one result on the page.
            if self.rows_on_page >= 2:
                return _('Displaying roles %(first_result)d to %(last_result)d of %(total_results)d matching '
                         '“%(search)s”',
                         first_result=self.first_row, last_result=self.last_row, total_results=self.total_rows,
                         search=search_term)

            # One result on the page.
            if self.rows_on_page == 1:
                return _('Displaying role %(result)d of %(total_results)d matching “%(search)s”',
                         result=self.first_row, total_results=self.total_rows, search=search_term)

            # No results.
            return _('No roles found matching “%(search)s”', search=search_term)

        # Text without a search.

        # More than one result on the page.
        if self.rows_on_page >= 2:
            return _('Displaying roles %(first_result)d to %(last_result)d of %(total_results)d',
                     first_result=self.first_row, last_result=self.last_row, total_results=self.total_rows)

        # One result on the page.
        if self.rows_on_page == 1:
            return _('Displaying role %(result)d of %(total_results)d',
                     result=self.first_row, total_results=self.total_rows)

        # No results.
        return _('No roles')
