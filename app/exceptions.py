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


class InvalidJWTokenPayloadError(AerariumError):
    """
        Raised when an :class:`app.token.JWToken` cannot be verified due to invalid payload.
    """
    pass
