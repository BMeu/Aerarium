#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Functions for handling JSON Web Tokens (JWT).
"""

from typing import Any
from typing import Dict
from typing import Optional

from time import time

from jwt import decode
from jwt import encode
from jwt import PyJWTError

from app import get_app


def get_token(**payload: Any) -> Optional[str]:
    """
        Get a JWT with the given payload. Use the token validity from the configuration.

        :Example:

        Calling ``get_token(user_id=10)`` will result in a payload of ``{user_id: 10}`` being used in the token (plus
        the expiration date).

        :param payload: Keyworded arguments for the payload.
        :return: The encoded JWT. ``None`` if called from outside the application context.
    """
    app = get_app()
    if app is None:
        return None

    validity = app.config['TOKEN_VALIDITY']
    expiration_date = time() + validity
    payload['exp'] = expiration_date

    token = encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token.decode('utf-8')


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
        Verify a JWT and return the payload (without the expiration field).

        :param token: The token to verify.
        :return: The payload as a dictionary. ``None`` if called from outside the application context or if decoding
                 fails.
    """
    app = get_app()
    if app is None:
        return None

    try:
        payload = decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except PyJWTError:
        return None

    payload.pop('exp', None)
    return payload
