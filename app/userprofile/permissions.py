#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Optional

from enum import Flag
from enum import unique

from flask_babel import lazy_gettext as _l

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

    EditRole = (1, _l('Edit Roles'), _l('The permission to create, read, update, or delete a role. '
                                        'This permission cannot be removed from a role if the role is the only one '
                                        'allowed to edit roles.'))
    """
        The permission to create, read, update, or delete a role.
    """

    EditUser = (2, _l('Edit Users'), _l('The permission to create, read, update, or delete a user.'))
    """
        The permission to create, read, update, or delete a user.
    """

    EditGlobalSettings = (4, _l('Edit Global Settings'), _l('The permission to modify the global settings.'))
    """
        The permission to read and update the global settings.
    """

    def __new__(cls, value: int, title: Optional[str] = None, description: Optional[str] = None) -> 'Permission':
        """
            Create an enum member with the given values.

            :param value: The enum member's actual value. Should be a power of two.
            :param title: A title used for displaying the enum member. If not given, the member's name will be used.
            :param description: An optional description used to display additional information about the permission.
            :return: The created enum member.
        """
        member = object.__new__(cls)

        member.description = description
        member.title = title

        # Set the actual underlying value and name.
        member._value_ = value

        return member

    def __init__(self, _value: int, _title: Optional[str] = None, _description: Optional[str] = None) -> None:
        """
            Initialize the enum member.

            :param _value: The enum member's actual value. Should be a power of two.
            :param _title: A title used for displaying the enum member. If not given, the member's name will be used.
            :param _description: An optional description used to display additional information about the permission.
        """

        # The parameters have been set in the __new__ method. Simply set the title to the member's name if the title is
        # not given. This cannot be done in __new__ as `name` is not yet defined in there.
        if not self.title:  # pragma: nocover
            # This will not be necessary here. But just in case...
            self.title = self.name

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
