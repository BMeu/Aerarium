#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Tokens for verifying user actions.
"""

from typing import Any
from typing import Optional

from flask_easyjwt import FlaskEasyJWT


class ChangeEmailAddressToken(FlaskEasyJWT):
    """
        A token for verifying requests to change a user's email address.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.user_id: Optional[int] = None
        """
            The ID of the user whose email address will be changed.
        """

        self.new_email: Optional[str] = None
        """
            The new email address to which the user wants to change.
        """


class DeleteAccountToken(FlaskEasyJWT):
    """
        A token for verifying requests to delete a user's account.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.user_id: Optional[int] = None
        """
            The ID of the user whose account will be deleted.
        """


class ResetPasswordToken(FlaskEasyJWT):
    """
        A token for verifying requests to change a user's password.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.user_id: Optional[int] = None
        """
            The ID of the user whose password will be reset.
        """
