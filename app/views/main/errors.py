#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The application's error routes.
"""

from flask import render_template
from flask_babel import gettext as _
from werkzeug.exceptions import HTTPException

from app.views.main import bp


# noinspection PyUnusedLocal
@bp.app_errorhandler(400)
def bad_request_error(error: HTTPException):
    """
        Return an error page for 400 - Bad Request errors.

        :param error: The exception causing this error.
        :return: The rendered error page.
    """
    title = _('Bad Request')
    message = _('Your request was malformed and could therefore not be handled by the server.')
    return render_template('error.html', title=title, message=message), 400


# noinspection PyUnusedLocal
@bp.app_errorhandler(401)
def unauthorized_access_error(error: HTTPException):
    """
        Return an error page for 401 - Unauthorized Access errors.

        :param error: The exception causing this error.
        :return: The rendered error page.
    """
    title = _('Unauthorized Access')
    message = _('The page you want to access requires you to login.')
    return render_template('error.html', title=title, message=message, show_login_link=True), 401


# noinspection PyUnusedLocal
@bp.app_errorhandler(403)
def permission_denied_error(error: HTTPException):
    """
        Return an error page for 403 - Permission Denied errors.

        :param error: The exception causing this error.
        :return: The rendered error page.
    """
    title = _('Permission Denied')
    message = _('''You do not have sufficient permissions to access this page. You can try logging in. If you are logged
                in and you still get this message, ask your administrator to raise your permissions.''')
    return render_template('error.html', title=title, message=message, show_login_link=True), 403


# noinspection PyUnusedLocal
@bp.app_errorhandler(404)
def page_not_found_error(error: HTTPException):
    """
        Return an error page for 404 - Page Not Found errors.

        :param error: The exception causing this error.
        :return: The rendered error page.
    """
    title = _('Page Not Found')
    message = _('''The page you requested was not found on the server. If you are positive the link you clicked is
                correct contact your administrator.''')
    return render_template('error.html', title=title, message=message), 404


# noinspection PyUnusedLocal
@bp.app_errorhandler(405)
def method_not_allowed_error(error: HTTPException):
    """
        Return an error page for 405 - Method Not Allowed errors.

        :param error: The exception causing this error.
        :return: The rendered error page.
    """
    title = _('Method Not Allowed')
    message = _('The HTTP method you used is not allowed to access this page.')
    return render_template('error.html', title=title, message=message), 405


# noinspection PyUnusedLocal
@bp.app_errorhandler(500)
def internal_error(error: HTTPException):
    """
        Return an error page for 500 - Internal Server Error errors.

        :param error: The exception causing this error.
        :return: The rendered error page.
    """
    title = _('Internal Error')
    message = _('''The server encountered an internal error while processing your request. Please try again later.
                The administrator has been notified.''')
    return render_template('error.html', title=title, message=message), 500
