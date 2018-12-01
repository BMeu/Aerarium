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
