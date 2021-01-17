# -*- coding: utf-8 -*-

"""
    A collection of tools for views.
"""

from flask import request
from werkzeug.urls import url_parse


def get_next_page(url_param: str = 'next', fallback_url: str = '/') -> str:
    """
        Get the URL for the next page from the URL parameters. If the next page is not given or is an invalid URL,
        return the URL for the home page.

        :param url_param: The URL parameter containing the URL for the next page. Defaults to ``next``.
        :param fallback_url: The URL that will be returned if the next page is not given in the URL params or the
                                  given URL is invalid. Defaults to the home page ``/``.
        :return: The URL for the next page.
    """

    next_page = request.args.get(url_param)
    if not next_page or url_parse(next_page).netloc != '':
        next_page = fallback_url

    return next_page
