# -*- coding: utf-8 -*-

"""
    Function decorators related to users and their profiles.
"""

from typing import Any
from typing import Callable

from functools import wraps

from flask import abort
from flask import url_for
from flask_login import current_user
from werkzeug.utils import redirect

from app.userprofile import Permission
from app.userprofile import User
from app.typing import ResponseType
from app.typing import ViewFunctionType


def logout_required(view_function: ViewFunctionType) -> ViewFunctionType:
    """
        A wrapper for view functions requiring the current user to be logged out. If the current user is logged in
        they will be redirected to the home page.

        :param view_function: The Flask view function being wrapped.
        :return: The wrapped view function.
    """

    @wraps(view_function)
    def wrapped_logout_required(*args: Any, **kwargs: Any) -> ResponseType:
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


def permission_required(permission: Permission) -> Callable[[ViewFunctionType], ViewFunctionType]:
    """
        A wrapper for view functions requiring the current user to have the given permission
        (:class:`app.userprofile.Permission`). If the user does not have the permission the request will be aborted with
        an error 403.

        This decorator does not check if the user is logged in.

        :param permission: The permission required to access the wrapped view.
        :return: The decorator for checking if the current user has the given permission.
    """

    # TODO: This should not be an alias of permission_required_all.
    return permission_required_all(permission)


def permission_required_all(*permissions: Permission) -> Callable[[ViewFunctionType], ViewFunctionType]:
    """
        A wrapper for view functions requiring the current user to have the given permissions
        (:class:`app.userprofile.Permission`). If the user does not have all of these permission the request will be
        aborted with an error 403.

        This decorator does not check if the user is logged in.

        :param permissions: The permissions required to access the wrapped view.
        :return: The decorator for checking if the current user has the given permission.
    """

    def permission_required_all_decorator(view_function: ViewFunctionType) -> ViewFunctionType:
        """
            The actual decorator for the view function.

            :param view_function: The Flask view being wrapped.
            :return: The wrapped view function.
        """

        @wraps(view_function)
        def wrapped_permission_required_all(*args: Any, **kwargs: Any) -> ResponseType:
            """
                If the current user does not have all of the requested permissions, abort with error 403. Otherwise,
                execute the wrapped view function.

                :param args: The arguments of the view function.
                :param kwargs: The keyword arguments of the view function.
                :return: The response of either an 403 error or the wrapped view function.
            """

            if not User.current_user_has_permissions_all(*permissions):
                return abort(403)

            return view_function(*args, **kwargs)

        return wrapped_permission_required_all

    return permission_required_all_decorator


def permission_required_one_of(*permissions: Permission) -> Callable[[ViewFunctionType], ViewFunctionType]:
    """
        A wrapper for view functions requiring the current user to have (at least) one of the given permissions
        (:class:`app.userprofile.Permission`). If the user does not have one of these permission the request will be
        aborted with an error 403.

        This decorator does not check if the user is logged in.

        :param permissions: The permissions required to access the wrapped view.
        :return: The decorator for checking if the current user has the given permission.
    """

    def permission_required_one_of_decorator(view_function: ViewFunctionType) -> ViewFunctionType:
        """
            The actual decorator for the view function.

            :param view_function: The Flask view being wrapped.
            :return: The wrapped view function.
        """

        @wraps(view_function)
        def wrapped_permission_required_one_of(*args: Any, **kwargs: Any) -> ResponseType:
            """
                If the current user does not have (at least) one of the requested permissions, abort with error 403.
                Otherwise, execute the wrapped view function.

                :param args: The arguments of the view function.
                :param kwargs: The keyword arguments of the view function.
                :return: The response of either an 403 error or the wrapped view function.
            """

            if not User.current_user_has_permissions_one_of(*permissions):
                return abort(403)

            return view_function(*args, **kwargs)

        return wrapped_permission_required_one_of

    return permission_required_one_of_decorator
