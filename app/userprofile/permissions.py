#!venv/bin/python
# -*- coding: utf-8 -*-

from enum import auto
from enum import Flag
from enum import unique

"""
    The permissions used within the application.
"""


@unique
class Permission(Flag):
    """
        An enumeration representing the permissions within the application.

        Each permission is represented by a value that is a power of two. Thus, combinations of permissions can be
        represented as an integer using bitwise operations.
    """

    EditRole = auto()
    """
        The permission to create, read, update, or delete a role.
    """

    EditUser = auto()
    """
        The permission to create, read, update, or delete a user.
    """

    EditGlobalSettings = auto()
    """
        The permission to read and update the global settings.
    """

    @staticmethod
    def bitwise_and(*permissions: 'Permission') -> 'Permission':
        """
            Perform a bitwise and on all given permissions.

            :param permissions: The permissions to perform the bitwise and on.
            :return: The resulting permission.
            :raise ValueError: if one of the permissions is `None`.
        """
        # Get all combinations at once as the basis for the and.
        result = Permission(-1)
        for permission in permissions:
            if permission is None:
                raise ValueError('None is not a valid permission')

            result &= permission

        return result

    @staticmethod
    def bitwise_or(*permissions: 'Permission') -> 'Permission':
        """
            Perform a bitwise or on all given permissions.

            :param permissions: The permissions to perform the bitwise or on.
            :return: The result permission.
            :raise ValueError: if one of the permissions is `None`.
        """
        result = Permission(0)
        for permission in permissions:
            if permission is None:
                raise ValueError('None is not a valid permission')

            result |= permission

        return result

    @staticmethod
    def bitwise_xor(*permissions: 'Permission') -> 'Permission':
        """
            Perform a bitwise xor on all given permissions.

            :param permissions: The permissions to perform the bitwise xor on.
            :return: The result permission.
            :raise ValueError: if one of the permissions is `None`.
        """
        result = Permission(0)
        for permission in permissions:
            if permission is None:
                raise ValueError('None is not a valid permission')

            result ^= permission

        return result
