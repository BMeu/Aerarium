#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from flask import abort

from app import create_app
from app.configuration import TestConfiguration


class ErrorsTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app.add_url_rule('/abort/<code>', 'abort', _aborting_route)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """
            Reset the test cases.
        """
        self.app_context.pop()

    def test_error_400(self):
        """
            Test the 400 - Bad Request error page.

            Expected result: The status code is 400 and the page contains information that the request mas malformed.
        """
        code = 400
        response = self.client.get('/abort/' + str(code))
        data = response.get_data(as_text=True)

        self.assertEqual(code, response.status_code)
        self.assertIn('Bad Request', data)

    def test_error_401(self):
        """
            Test the 401 - Unauthorized Access error page.

            Expected result: The status code is 401 and the page contains information that the user is not logged in.
        """
        code = 401
        response = self.client.get('/abort/' + str(code))
        data = response.get_data(as_text=True)

        self.assertEqual(code, response.status_code)
        self.assertIn('Unauthorized Access', data)

        # TODO: Check for login link in page.

    def test_error_403(self):
        """
            Test the 403 - Permission Denied error page.

            Expected result: The status code is 403 and the page contains information that the permission was denied.
        """
        code = 403
        response = self.client.get('/abort/' + str(code))
        data = response.get_data(as_text=True)

        self.assertEqual(code, response.status_code)
        self.assertIn('Permission Denied', data)

        # TODO: Check for login link in page.

    def test_error_404(self):
        """
            Test the 404 - Page Not Found error page.

            Expected result: The status code is 404 and the page contains information that the requested page was not
                             found.
        """
        code = 404
        response = self.client.get('/abort/' + str(code))
        data = response.get_data(as_text=True)

        self.assertEqual(code, response.status_code)
        self.assertIn('Page Not Found', data)

    def test_error_405(self):
        """
            Test the 405 - Method Not Allowed error page.

            Expected result: The status code is 405 and the page contains information that the HTTP method is not
                             allowed.
        """
        code = 405
        response = self.client.get('/abort/' + str(code))
        data = response.get_data(as_text=True)

        self.assertEqual(code, response.status_code)
        self.assertIn('Method Not Allowed', data)

    def test_error_500(self):
        """
            Test the 500 - Internal Server Error error page.

            Expected result: The status code is 500 and the page contains information that the server encountered an
                             internal error.
        """
        code = 500
        response = self.client.get('/abort/' + str(code))
        data = response.get_data(as_text=True)

        self.assertEqual(code, response.status_code)
        self.assertIn('Internal Error', data)


def _aborting_route(code):
    """
        A simple view function aborting with the given ``code``.
    """
    abort(int(code))
