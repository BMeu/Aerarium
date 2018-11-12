#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Tokens for verifying user actions.
"""

from app.token import JWToken


class ChangeEmailAddressToken(JWToken):
    """
        A token for verifying requests to change a user's email address.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_id: int = None
        """
            The ID of the user whose email address will be changed.
        """

        self.new_email: str = None
        """
            The new email address to which the user wishes to change.
        """


class DeleteAccountToken(JWToken):
    """
        A token for verifying requests to delete a user's account.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_id: int = None
        """
            The ID of the user whose account will be deleted.
        """


class ResetPasswordToken(JWToken):
    """
        A token for verifying requests to change a user's password.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_id: int = None
        """
            The ID of the user whose password will be reset.
        """
