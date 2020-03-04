# -*- coding: utf-8 -*-

from flask import url_for

from tests.views import ViewTestCase


class ErrorsTest(ViewTestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """

        super().setUp()

        # Add a view that aborts with the given code.
        self.app.add_url_rule('/abort/<int:code>', 'abort', self.aborting_route)

    def test_error_400(self):
        """
            Test the 400 - Bad Request error page.

            Expected result: The status code is 400 and the page contains information that the request mas malformed.
        """

        code = 400
        data = self.get(f'/abort/{code}', expected_status=code)

        self.assertIn('Bad Request', data)

    def test_error_401(self):
        """
            Test the 401 - Unauthorized Access error page.

            Expected result: The status code is 401 and the page contains information that the user is not logged in.
        """

        code = 401
        data = self.get(f'/abort/{code}', expected_status=code)

        self.assertIn('Unauthorized Access', data)

        # Ensure that the login page is linked.
        self.assertIn(url_for('userprofile.login'), data)

    def test_error_403(self):
        """
            Test the 403 - Permission Denied error page.

            Expected result: The status code is 403 and the page contains information that the permission was denied.
        """

        code = 403
        data = self.get(f'/abort/{code}', expected_status=code)

        self.assertIn('Permission Denied', data)

        # Ensure that the login page is linked.
        self.assertIn(url_for('userprofile.login'), data)

    def test_error_404(self):
        """
            Test the 404 - Page Not Found error page.

            Expected result: The status code is 404 and the page contains information that the requested page was not
                             found.
        """

        code = 404
        data = self.get(f'/abort/{code}', expected_status=code)

        self.assertIn('Page Not Found', data)

    def test_error_405(self):
        """
            Test the 405 - Method Not Allowed error page.

            Expected result: The status code is 405 and the page contains information that the HTTP method is not
                             allowed.
        """

        code = 405
        data = self.get(f'/abort/{code}', expected_status=code)

        self.assertIn('Method Not Allowed', data)

    def test_error_500(self):
        """
            Test the 500 - Internal Server Error error page.

            Expected result: The status code is 500 and the page contains information that the server encountered an
                             internal error.
        """

        code = 500
        data = self.get(f'/abort/{code}', expected_status=code)

        self.assertIn('Internal Error', data)
