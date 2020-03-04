# -*- coding: utf-8 -*-

from unittest.mock import MagicMock
from unittest.mock import patch

from tests.views import ViewTestCase


class AuthenticationTest(ViewTestCase):

    # region Login

    def test_login_get_logged_out(self):
        """
            Test accessing the login page with an anonymous user.

            Expected result: The user is displayed the login form.
        """

        data = self.get('/user/login')

        self.assertIn('<h1>Log In</h1>', data)
        self.assertIn('<form', data)

    def test_login_get_logged_in(self):
        """
            Test accessing the login page with an authorized user.

            Expected result: The user is redirected to the homepage.
        """

        self.create_and_login_user()

        data = self.get('/user/login')

        self.assertNotIn('<h1>Log In</h1>', data)
        self.assertIn('<h1>Dashboard</h1>', data)

    def test_login_post_success(self):
        """
            Test logging in with valid credentials.

            Expected result: The login succeeds, the user is redirected to the home page and greeted.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        self.create_user(email, name, password)

        data = self.post('/user/login', data=dict(
            email=email,
            password=password
        ))

        self.assertNotIn('<h1>Log In</h1>', data)
        self.assertIn('<h1>Dashboard</h1>', data)
        self.assertIn(f'Welcome, {name}!', data)

    def test_login_post_success_with_next_page(self):
        """
            Test logging in with valid credentials and a given next page.

            Expected result: The login succeeds, the user is redirected to the given next page and greeted.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        self.create_user(email, name, password)

        data = self.post('/user/login?next=user', expected_status=404, data=dict(
            email=email,
            password=password
        ))

        self.assertNotIn('<h1>Log In</h1>', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)
        self.assertIn(f'Welcome, {name}!', data)
        self.assertIn(f'User Profile', data)

    def test_login_post_failure(self):
        """
            Test logging in with invalid credentials.

            Expected result: The login fails and the user stays on the login page.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        self.create_user(email, name, password)

        data = self.post('/user/login', data=dict(
            email=email,
            password='invalid' + password
        ))

        self.assertIn('<h1>Log In</h1>', data)
        self.assertIn('Invalid email address or password.', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)

    # endregion

    # region Refresh Login

    def test_login_refresh_get_fresh(self):
        """
            Test accessing the login refresh page with a freshly authorized user.

            Expected result: The user is redirected to the home page.
        """

        self.create_and_login_user()

        data = self.get('/user/login/refresh')

        self.assertNotIn('<h1>Confirm Login</h1>', data)
        self.assertIn('<h1>Dashboard</h1>', data)

    @patch('app.views.userprofile.authentication.login_fresh')
    def test_login_refresh_get_stale(self, mock_login_fresh: MagicMock):
        """
            Test accessing the login refresh page with a stale login.

            Expected result: The refresh login page is shown.
        """

        mock_login_fresh.return_value = False

        self.create_and_login_user()

        data = self.get('/user/login/refresh')

        self.assertIn('<h1>Confirm Login</h1>', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)

    @patch('app.views.userprofile.authentication.login_fresh')
    def test_login_refresh_post_invalid_password(self, mock_login_fresh: MagicMock):
        """
            Test refreshing the login with an invalid password.

            Expected result: The refresh login page is shown, the login is not refreshed.
        """

        mock_login_fresh.return_value = False

        password = 'ABC123!'
        self.create_and_login_user(password=password)

        data = self.post('/user/login/refresh', data=dict(
            password='invalid' + password
        ))

        self.assertIn('<h1>Confirm Login</h1>', data)
        self.assertIn('Invalid password', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)

    @patch('app.views.userprofile.authentication.login_fresh')
    def test_login_refresh_post_valid_password(self, mock_login_fresh: MagicMock):
        """
            Test refreshing the login with a valid password.

            Expected result: The refresh home page is shown, the login is refreshed.
        """

        mock_login_fresh.return_value = False

        password = 'ABC123!'
        user = self.create_and_login_user(password=password)

        data = self.post('/user/login/refresh', data=dict(
            password=password
        ))

        self.assertNotIn('<h1>Confirm Login</h1>', data)
        self.assertNotIn('Invalid password', data)
        self.assertIn(f'Welcome, {user.name}!', data)
        self.assertIn('<h1>Dashboard</h1>', data)

    # endregion

    # region Logout

    def test_logout_logged_in(self):
        """
            Test logging out with a logged in user.

            Expected result: The user is logged out, redirected to the home page (and from there to the login page),
                             and shown a success message.
        """

        self.create_and_login_user()

        data = self.get('/user/logout')

        self.assertIn('You were successfully logged out.', data)
        self.assertIn('<h1>Log In</h1>', data)

    def test_logout_logged_out(self):
        """
            Test logging out with an anonymous user.

            Expected result: The user is redirected to the home page (and from there to the login page),
                             but not shown a success message.
        """

        data = self.get('/user/logout')

        self.assertNotIn('You were successfully logged out.', data)
        self.assertIn('<h1>Log In</h1>', data)

    # endregion
