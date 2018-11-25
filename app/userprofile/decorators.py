#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Function decorators related to a user's profile.
"""

from typing import Any
from typing import Callable

from functools import wraps

from flask import url_for
from flask_login import current_user
from werkzeug.utils import redirect


def logout_required(view_function: Callable[..., str]) -> Callable[..., str]:
    """
        A wrapper for view functions requiring the current user to be logged out. If the current user is logged in
        they will be redirected to the home page.

        :param view_function: The Flask view function being wrapped.
        :return: The wrapped view function.
    """

    @wraps(view_function)
    def wrapped_logout_required(*args: Any, **kwargs: Any) -> str:
        """
            If the current user is logged in, redirect to the home page. Otherwise, execute the wrapped view function.

            :param args: The arguments of the view function.
            :param kwargs: The keyword arguments of the view function.
            :return: The response of either the home page view function or the wrapped view function.
        """
        if current_user is not None and current_user.is_authenticated:
            return redirect(url_for('main.index'))

        return view_function(*args, **kwargs)

    return wrapped_logout_required
