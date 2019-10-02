#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app import mail
from app.configuration import TestConfiguration
from app.userprofile import User
from app.userprofile.tokens import ResetPasswordToken


class PasswordResetTest(TestCase):

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

    # region Request

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

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/reset-password', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('Forgot Your Password?', data)

    def test_reset_password_request_get_logged_out(self):
        """
            Test accessing the password reset request form via GET when logged out.

            Expected result: The password reset request form is displayed.
        """
        response = self.client.get('/user/reset-password', follow_redirects=True)
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
            response = self.client.post('/user/reset-password', follow_redirects=True, data=dict(
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
            response = self.client.post('/user/reset-password', follow_redirects=True, data=dict(
                email=email
            ))
            data = response.get_data(as_text=True)

            self.assertEqual(0, len(outgoing))

            self.assertIn('<h1>Log In</h1>', data)
            self.assertIn('An email has been sent to the specified address.', data)

    # endregion

    # region Execution

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

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        response = self.client.get(f'/user/reset-password/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('The token is invalid.', data)
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

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        response = self.client.get(f'/user/reset-password/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Reset Your Password', data)
        self.assertIn('New Password', data)
        self.assertNotIn('The token is invalid.', data)
        self.assertIn('Confirm Your New Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_get_failure_invalid_token(self):
        """
            Test accessing the password reset form with an anonymous user and an invalid token.

            Expected result: A 404 error page is shown.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        response = self.client.get('/user/reset-password/just-some-token', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertEqual(404, response.status_code)
        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_get_failure_no_user(self):
        """
            Test accessing the password reset form with an anonymous user and a token for a non-existing user.

            Expected result: A 404 error page is shown.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        db.session.delete(user)
        db.session.commit()

        response = self.client.get(f'/user/reset-password/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertEqual(404, response.status_code)
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

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        new_password = 'abcdef'
        response = self.client.post(f'/user/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('The token is invalid.', data)
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

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        new_password = 'abcdef'
        response = self.client.post(f'/user/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))
        data = response.get_data(as_text=True)

        self.assertNotIn('Reset Your Password', data)
        self.assertIn('Log In', data)
        self.assertNotIn('The token is invalid.', data)
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

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        new_password = 'abcdef'
        response = self.client.post(f'/user/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password + 'ghi'
        ))
        data = response.get_data(as_text=True)

        self.assertIn('Reset Your Password', data)
        self.assertNotIn('The token is invalid.', data)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    def test_reset_password_post_failure_invalid_token(self):
        """
            Test posting to the password reset form with an anonymous user, an invalid token, and a valid form.

            Expected result: The password is not updated and the user is shown a 404 error page.
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
        response = self.client.post('/user/reset-password/just-some-token', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))
        data = response.get_data(as_text=True)

        self.assertEqual(404, response.status_code)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    def test_reset_password_post_failure_no_user(self):
        """
            Test posting to the password reset form with an anonymous user, a token for a non-existing user, and a valid
            form.

            Expected result: The password is not updated and the user is shown a 404 error page.
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

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        db.session.delete(user)
        db.session.commit()

        new_password = 'abcdef'
        response = self.client.post(f'/user/reset-password/{token}', follow_redirects=True, data=dict(
            password=new_password,
            password_confirmation=new_password + 'ghi'
        ))
        data = response.get_data(as_text=True)

        self.assertEqual(404, response.status_code)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    # endregion
