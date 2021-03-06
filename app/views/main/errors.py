# -*- coding: utf-8 -*-

"""
    The application's error routes.
"""

from flask import render_template
from flask_babel import gettext as _
from werkzeug.exceptions import HTTPException

from app.views.main import bp
from app.typing import ResponseType


@bp.app_errorhandler(400)  # type: ignore
def bad_request_error(_error: HTTPException) -> ResponseType:
    """
        Return an error page for ``400 - Bad Request`` errors.

        :param _error: The exception causing this error.
        :return: The rendered error page.
    """

    title = _('Bad Request')
    message = _('Your request was malformed and could therefore not be handled by the server.')
    return render_template('error.html', title=title, message=message), 400


@bp.app_errorhandler(401)  # type: ignore
def unauthorized_access_error(_error: HTTPException) -> ResponseType:
    """
        Return an error page for ``401 - Unauthorized Access`` errors.

        :param _error: The exception causing this error.
        :return: The rendered error page.
    """

    title = _('Unauthorized Access')
    message = _('The page you want to access requires you to login.')
    return render_template('error.html', title=title, message=message, show_login_link=True), 401


@bp.app_errorhandler(403)  # type: ignore
def permission_denied_error(_error: HTTPException) -> ResponseType:
    """
        Return an error page for ``403 - Permission Denied`` errors.

        :param _error: The exception causing this error.
        :return: The rendered error page.
    """

    title = _('Permission Denied')
    message = _('''You do not have sufficient permissions to access this page. You can try logging in. If you are logged
                in and you still get this message, ask your administrator to raise your permissions.''')
    return render_template('error.html', title=title, message=message, show_login_link=True), 403


@bp.app_errorhandler(404)  # type: ignore
def page_not_found_error(_error: HTTPException) -> ResponseType:
    """
        Return an error page for ``404 - Page Not Found`` errors.

        :param _error: The exception causing this error.
        :return: The rendered error page.
    """

    title = _('Page Not Found')
    message = _('''The page you requested was not found on the server. If you are positive the link you clicked is
                correct contact your administrator.''')
    return render_template('error.html', title=title, message=message), 404


@bp.app_errorhandler(405)  # type: ignore
def method_not_allowed_error(_error: HTTPException) -> ResponseType:
    """
        Return an error page for ``405 - Method Not Allowed`` errors.

        :param _error: The exception causing this error.
        :return: The rendered error page.
    """

    title = _('Method Not Allowed')
    message = _('The HTTP method you used is not allowed to access this page.')
    return render_template('error.html', title=title, message=message), 405


@bp.app_errorhandler(500)  # type: ignore
def internal_error(_error: HTTPException) -> ResponseType:
    """
        Return an error page for ``500 - Internal Server Error`` errors.

        :param _error: The exception causing this error.
        :return: The rendered error page.
    """

    title = _('Internal Error')
    message = _('''The server encountered an internal error while processing your request. Please try again later.
                The administrator has been notified.''')
    return render_template('error.html', title=title, message=message), 500
