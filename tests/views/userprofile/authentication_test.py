#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import User


class AuthenticationTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    # region Login

    def test_login_get_logged_out(self):
        """
            Test accessing the login page with an anonymous user.

            Expected result: The user is displayed the login form.
        """
        response = self.client.get('/user/login', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('<h1>Log In</h1>', data)
        self.assertIn('<form', data)

    def test_login_get_logged_in(self):
        """
            Test accessing the login page with an authorized user.

            Expected result: The user is redirected to the homepage.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/login', follow_redirects=True)
        data = response.get_data(as_text=True)

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
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        response = self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))
        data = response.get_data(as_text=True)

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
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        response = self.client.post('/user/login?next=some-other-page', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))
        data = response.get_data(as_text=True)

        self.assertNotIn('<h1>Log In</h1>', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)
        self.assertIn(f'Welcome, {name}!', data)

    def test_login_post_failure(self):
        """
            Test logging in with invalid credentials.

            Expected result: The login fails and the user stays on the login page.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        response = self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password='invalid' + password
        ))
        data = response.get_data(as_text=True)

        self.assertIn('<h1>Log In</h1>', data)
        self.assertIn('Invalid email address or password.', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)

    # endregion

    # region Refresh Login

    def test_login_refresh_get_fresh(self):
        """
            Test accessing the login refresh page with an freshly authorized user.

            Expected result: The user is redirected to the home page.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/login/refresh', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertNotIn('<h1>Confirm Login</h1>', data)
        self.assertIn('<h1>Dashboard</h1>', data)

    @patch('app.views.userprofile.authentication.login_fresh')
    def test_login_refresh_get_stale(self, mock_login_fresh: MagicMock):
        """
            Test accessing the login refresh page with a stale login.

            Expected result: The refresh login page is shown.
        """
        mock_login_fresh.return_value = False

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/login/refresh', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('<h1>Confirm Login</h1>', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)

    @patch('app.views.userprofile.authentication.login_fresh')
    def test_login_refresh_post_invalid_password(self, mock_login_fresh: MagicMock):
        """
            Test refreshing the login with an invalid password.

            Expected result: The refresh login page is shown, the login is not refreshed.
        """
        mock_login_fresh.return_value = False

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post('/user/login/refresh', follow_redirects=True, data=dict(
            password='invalid' + password
        ))
        data = response.get_data(as_text=True)

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

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post('/user/login/refresh', follow_redirects=True, data=dict(
            password=password
        ))
        data = response.get_data(as_text=True)

        self.assertNotIn('<h1>Confirm Login</h1>', data)
        self.assertNotIn('Invalid password', data)
        self.assertIn(f'Welcome, {name}!', data)
        self.assertIn('<h1>Dashboard</h1>', data)

    # endregion

    # region Logout

    def test_logout_logged_in(self):
        """
            Test logging out with a logged in user.

            Expected result: The user is logged out, redirected to the home page (and from there to the login page),
                             and shown a success message.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/logout', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('You were successfully logged out.', data)
        self.assertIn('<h1>Log In</h1>', data)

    def test_logout_logged_out(self):
        """
            Test logging out with an anonymous user.

            Expected result: The user is redirected to the home page (and from there to the login page),
                             but not shown a success message.
        """
        response = self.client.get('/user/logout', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertNotIn('You were successfully logged out.', data)
        self.assertIn('<h1>Log In</h1>', data)

    # endregion
