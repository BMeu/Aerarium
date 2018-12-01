#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Optional

from app import db
from app.userprofile import Permission

"""
    The application's role model.
"""


class Role(db.Model):
    """
        The class representing a role with certain permissions.
    """

    # region Fields

    id = db.Column(db.Integer, primary_key=True)
    """
        The role's unique ID.
    """

    name = db.Column(db.String(255), unique=True)
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

    # endregion

    # region Initialization

    @staticmethod
    def load_from_id(role_id: int) -> Optional['Role']:
        """
            Load the role with the given ID from the database.

            :param role_id: The ID of the role to load.
            :return: The loaded role if it exists, `None` otherwise.
        """
        return Role.query.get(role_id)

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

        return Permission(self._permissions)

    @permissions.setter
    def permissions(self, permission: Permission) -> None:
        """
            Set the given permissions for this role.

            This will overwrite all existing permissions.

            :param permission: An enum member of :class:`Permission` representing the role`s new permissions (may be a
                          combination of multiple enum members).
        """
        if permission is None:
            permission = Permission(0)

        self._permissions = permission.value

    def has_permission(self, permission: Permission) -> bool:
        """
            Determine if the role has the given permission.

            Alias of :meth:`has_permissions_all` with only a single permission.

            :param permission: The permission to check for.
            :return: `True` if the role has the requested permission, `False` otherwise.
        """
        return self.has_permissions_all(permission)

    def has_permissions_all(self, *permissions: Permission) -> bool:
        """
            Determine if the role has all of the given permissions.

            If the empty permission `Permission(0)` is given, the result will always be `False`.

            :param permissions: The permissions to check for.
            :return: `True` if the role has all of the requested permissions, `False` otherwise.
        """
        permission = Permission.bitwise_or(*permissions)

        if permission.value == 0:
            return False

        return permission & self.permissions == permission

    def has_permissions_one_of(self, *permissions: Permission) -> bool:
        """
            Determine if the role has (at least) one of the given permissions.

            If the empty permission `Permission(0)` is given, the result will always be `False`.

            :param permissions: The permissions to check for.
            :return: `True` if the role has one of the requested permission, `False` otherwise.
        """
        has_permission = False
        for permission in permissions:
            if permission == Permission(0):
                continue

            has_permission = has_permission or self.has_permission(permission)

        return has_permission

    def add_permissions(self, *permissions: Permission) -> None:
        """
            Add the given permission to this role.

            Existing permissions will be kept.

            :param permissions: The permissions that will be added to the role.
        """
        self.permissions = Permission.bitwise_or(self.permissions, *permissions)

    def remove_permission(self, permission: Permission) -> None:
        """
            Remove a permission from this role.

            Other permissions will be kept.

            :param permission: The :class:`Permission` that will be removed from the role.
        """
        if permission is None:
            raise ValueError('None is not a valid permission')

        # If the permission is not set, do nothing
        # (otherwise, the bitwise difference ^ would add the permission).
        if not self.has_permission(permission):
            return

        self.permissions ^= permission

    # endregion

    # region System

    def __repr__(self) -> str:
        """
            Get a string representation of the role.

            :return: A string representation of the role.
        """
        return f'<Role [{self.id}] "{self.name}" [{self.permissions}]>'

    # endregion
