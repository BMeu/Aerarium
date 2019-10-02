#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Exceptions raised by Aerarium.
"""


class AerariumError(Exception):
    """
        Base class for all exceptions raised by Aerarium.
    """
    pass


class DeletionPreconditionViolationError(AerariumError):
    """
        Raised if a :class:`app.userprofile.Role` cannot be deleted because some precondition failed.
    """
    pass


class NoApplicationError(AerariumError):
    """
        Raised if the application object is accessed outside the application context
    """
    pass


class NoMailSenderError(AerariumError):
    """
        Raised when an :class:`app.email.Email` does not have a sender.
    """
    pass
