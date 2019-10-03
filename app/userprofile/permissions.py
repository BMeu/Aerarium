# -*- coding: utf-8 -*-

"""
    The permissions used within the application.
"""

from typing import cast
from typing import Optional

from enum import Flag

from flask_babel import lazy_gettext as _l

from app.tools.math import is_power_of_two


class PermissionBase(Flag):
    """
        The basic enumeration definition for permissions.

        Each permission is represented by a value that is a power of two. Thus, combinations of permissions can be
        represented as an integer using bitwise operations. Enumeration members must not (and cannot) have a value
        that is not a power of two. Furthermore, values must be unique.

        The permission with the value ``0``, ``Permission(0)``, is called the *empty permission*.
    """

    def __new__(cls, value: int, _title: Optional[str] = None, _description: Optional[str] = None) -> 'PermissionBase':
        """
            Create an enum member with the given values.

            :param value: The enum member's actual value. Must be a power of two.
            :param _title: A title that can be used for displaying the enum member. If not given, the member's name will
                           be set as the title.
            :param _description: An optional description that can be used to display additional information about the
                                 permission.
            :return: The created enum member.
        """

        # Ensure the given value is a power of 2.
        if not is_power_of_two(value):
            raise ValueError('Permission values must be a power of 2')

        # Create the actual member.
        member = object.__new__(cls)
        member._value_ = value

        return cast('Permission', member)

    def __init__(self, value: int, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """
            :param value: The enum member's actual value. Must be a power of two.
            :param title: A title that can be used for displaying the enum member. If not given, the member's name will
                          be set as the title.
            :param description: An optional description that can be used to display additional information about the
                                permission.
            :raise ValueError: If the value is not a power of two or if the value has already been defined for another
                               member.
        """

        # Ensure that this value has not been defined before.
        for existing_member in self.__class__.__members__.values():
            if value == existing_member.value:
                raise ValueError(f'Duplicate permission value found: {repr(self)} -> {repr(existing_member)}')

        # Set the title to the member's name if it has not been given explicitly.
        if title is None:
            title = self.name

        self.title = title
        self.description = description


class Permission(PermissionBase):
    """
        An enumeration representing the permissions within the application.
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
