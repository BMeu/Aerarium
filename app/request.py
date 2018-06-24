#!venv/bin/python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import g
from flask import Response
from flask_babel import get_locale

from app.configuration import BaseConfiguration

"""
    Functions modifying the request on application level.
"""


def register_after_request_handlers(application: Flask) -> None:
    """
        Register handlers that will be executed after each request.

        :param application: The application instance for which the handlers will be registered.
    """
    application.after_request(_header_x_clacks_overhead)


def register_before_request_handlers(application: Flask) -> None:
    """
        Register handlers that will be executed before each request.

        :param application: The application instance for which the handlers will be registered.
    """
    application.before_request(_extend_global_variable)


def _extend_global_variable() -> None:
    """
        Extend the global variable ``g`` with further information:

         * ``g.locale``: The current locale (e.g. ``en-US`` or ``de``).
         * ``g.title``: The app title.
    """
    g.locale = get_locale()
    g.title = BaseConfiguration.TITLE_SHORT


def _header_x_clacks_overhead(response: Response) -> Response:
    """
        Add an X-Clacks-Overhead field to the ``response``'s header.

        In memoriam Terry Pratchett.

        :see: http://www.gnuterrypratchett.com/

        :param response: The response to which the header field will be added.
        :return: The extended response.
    """
    response.headers.add('X-Clacks-Overhead', 'GNU Terry Pratchett')
    return response
