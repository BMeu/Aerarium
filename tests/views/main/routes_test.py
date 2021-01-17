# -*- coding: utf-8 -*-

from tests.views import ViewTestCase


class RoutesTest(ViewTestCase):

    def test_index_logged_out(self):
        """
            Test the dashboard without an anonymous user.

            Expected result: The user is redirected to the login page.
        """

        data = self.get('/')

        self.assertNotIn('<h1>Dashboard</h1>', data)
        self.assertIn('<h1>Log In</h1>', data)

    def test_index_logged_in(self):
        """
            Test accessing the dashboard with a logged in user.

            Expected result: The user is shown the dashboard.
        """

        self.create_and_login_user()

        data = self.get('/')

        self.assertIn('<h1>Dashboard</h1>', data)
        self.assertNotIn('<h1>Log In</h1>', data)
