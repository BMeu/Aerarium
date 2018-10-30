#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app import mail
from app.authorization import User
from app.configuration import TestConfiguration


class RoutesTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_get_logged_out(self):
        """
            Test accessing the login page with an anonymous user.

            Expected result: The user is displayed the login form.
        """
        response = self.client.get('/login', follow_redirects=True)
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

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/login', follow_redirects=True)
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

        response = self.client.post('/login', follow_redirects=True, data=dict(
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

        response = self.client.post('/login?next=some-other-page', follow_redirects=True, data=dict(
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

        response = self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password='invalid' + password
        ))
        data = response.get_data(as_text=True)

        self.assertIn('<h1>Log In</h1>', data)
        self.assertIn('Invalid email address or password.', data)
        self.assertNotIn('<h1>Dashboard</h1>', data)

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

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('You were successfully logged out.', data)
        self.assertIn('<h1>Log In</h1>', data)

    def test_logout_logged_out(self):
        """
            Test logging out with an anonymous user.

            Expected result: The user is redirected to the home page (and from there to the login page),
                             but not shown a success message.
        """
        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertNotIn('You were successfully logged out.', data)
        self.assertIn('<h1>Log In</h1>', data)

    def test_reset_password_request_logged_in(self):
        """
            Test accessing the password reset request form with a user who is logged in.

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

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/reset-password', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('Forgot Your Password?', data)

    def test_reset_password_request_get_logged_out(self):
        """
            Test accessing the password reset request form via GET when logged out.

            Expected result: The password reset request form is displayed.
        """
        response = self.client.get('/reset-password', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Forgot Your Password?', data)

    def test_reset_password_request_post_existing_user(self):
        """
            Test accessing the password reset request form via POST with an existing user.

            Expected result: The password reset mail is sent to the user and a message is displayed.
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

        with mail.record_messages() as outgoing:
            response = self.client.post('/reset-password', follow_redirects=True, data=dict(
                email=email
            ))
            data = response.get_data(as_text=True)

            self.assertEqual(1, len(outgoing))
            self.assertIn('Reset Your Password', outgoing[0].subject)

            self.assertIn('<h1>Log In</h1>', data)
            self.assertIn('An email has been sent to the specified address.', data)

    def test_reset_password_request_post_non_existing_user(self):
        """
            Test accessing the password reset request form via POST with a non-existing user.

            Expected result: No password reset mail is sent, but a message is displayed that it has.
        """
        email = 'test@example.com'

        with mail.record_messages() as outgoing:
            response = self.client.post('/reset-password', follow_redirects=True, data=dict(
                email=email
            ))
            data = response.get_data(as_text=True)

            self.assertEqual(0, len(outgoing))

            self.assertIn('<h1>Log In</h1>', data)
            self.assertIn('An email has been sent to the specified address.', data)

    def test_reset_password_get_logged_in(self):
        """
            Test accessing the password reset form with a user who is logged in, and a valid token.

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

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        token = user.get_password_reset_token()
        self.assertIsNotNone(token)

        response = self.client.get(f'/reset-password/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('Reset Your Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_get_success(self):
        """
            Test accessing the password reset form with an anonymous user and a valid token.

            Expected result: The user password reset form is displayed.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        token = user.get_password_reset_token()
        self.assertIsNotNone(token)

        response = self.client.get(f'/reset-password/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Reset Your Password', data)
        self.assertIn('New Password', data)
        self.assertIn('Confirm Your New Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_get_failure_invalid_token(self):
        """
            Test accessing the password reset form with an anonymous user and an invalid token.

            Expected result: The user is redirected to the home page.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        response = self.client.get('/reset-password/just-some-token', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertNotIn('Reset Your Password', data)
        self.assertIn('Dashboard', data)
        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_post_logged_in(self):
        """
            Test posting to the password reset form with a user who is logged in, and a valid token.

            Expected result: The user is redirected to the home page without changing the password.
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

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        token = user.get_password_reset_token()
        self.assertIsNotNone(token)

        new_password = 'abcdef'
        response = self.client.post(f'/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('Reset Your Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertTrue(user.check_password(password))

    def test_reset_password_post_success(self):
        """
            Test posting to the password reset form with an anonymous user, a valid token, and a valid form.

            Expected result: The password is set to the new one and the user is redirected to the login page.
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

        token = user.get_password_reset_token()
        self.assertIsNotNone(token)

        new_password = 'abcdef'
        response = self.client.post(f'/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))
        data = response.get_data(as_text=True)

        self.assertNotIn('Reset Your Password', data)
        self.assertIn('Log In', data)
        self.assertIn('Your password has successfully been changed.', data)
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password(password))

    def test_reset_password_post_failure_invalid_input(self):
        """
            Test posting to the password reset form with an anonymous user, a valid token, and an invalid form.

            Expected result: The password is not updated and the user is shown the reset password form.
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

        token = user.get_password_reset_token()
        self.assertIsNotNone(token)

        new_password = 'abcdef'
        response = self.client.post(f'/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password + 'ghi'
        ))
        data = response.get_data(as_text=True)

        self.assertIn('Reset Your Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    def test_reset_password_post_failure_invalid_token(self):
        """
            Test posting to the password reset form with an anonymous user, an invalid token, and a valid form.

            Expected result: The password is not updated and the user is redirected to the home page.
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

        new_password = 'abcdef'
        response = self.client.post('/reset-password/just-some-token', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))
        data = response.get_data(as_text=True)

        self.assertIn('Log In', data)
        self.assertNotIn('Reset Your Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))
