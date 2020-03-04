# -*- coding: utf-8 -*-

from app import db
from app import mail
from app.userprofile.tokens import ResetPasswordToken
from tests.views import ViewTestCase


class PasswordResetTest(ViewTestCase):

    def test_reset_password_request_logged_in(self):
        """
            Test accessing the password reset request form with a user who is logged in.

            Expected result: The user is redirected to the home page.
        """

        self.create_and_login_user()

        data = self.get('/user/reset-password')

        self.assertIn('Dashboard', data)
        self.assertNotIn('Forgot Your Password?', data)

    def test_reset_password_request_get_logged_out(self):
        """
            Test accessing the password reset request form via GET when logged out.

            Expected result: The password reset request form is displayed.
        """

        data = self.get('/user/reset-password')

        self.assertIn('Forgot Your Password?', data)

    def test_reset_password_request_post_existing_user(self):
        """
            Test accessing the password reset request form via POST with an existing user.

            Expected result: The password reset mail is sent to the user and a message is displayed.
        """

        email = 'test@example.com'
        self.create_user(email=email, name='Jane Doe', password='ABC123!')

        with mail.record_messages() as outgoing:
            data = self.post('/user/reset-password', data=dict(
                email=email
            ))

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
            data = self.post('/user/reset-password', data=dict(
                email=email
            ))

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

        user = self.create_and_login_user()

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        data = self.get(f'/user/reset-password/{token}')

        self.assertIn('Dashboard', data)
        self.assertNotIn('The token is invalid.', data)
        self.assertNotIn('Reset Your Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_get_success(self):
        """
            Test accessing the password reset form with an anonymous user and a valid token.

            Expected result: The user password reset form is displayed.
        """

        user = self.create_user(email='doe@example.com', name='Jane', password='ABC123!')

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        data = self.get(f'/user/reset-password/{token}')

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

        self.create_user(email='test@example.com', name='John Doe', password='ABC123!')

        data = self.get('/user/reset-password/just-some-token', expected_status=404)

        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_get_failure_no_user(self):
        """
            Test accessing the password reset form with an anonymous user and a token for a non-existing user.

            Expected result: A 404 error page is shown.
        """

        user = self.create_user(email='doe@example.com', name='Jane', password='ABC123!')

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        db.session.delete(user)
        db.session.commit()

        data = self.get(f'/user/reset-password/{token}', expected_status=404)

        self.assertNotIn('Your password has successfully been changed.', data)

    def test_reset_password_post_logged_in(self):
        """
            Test posting to the password reset form with a user who is logged in, and a valid token.

            Expected result: The user is redirected to the home page without changing the password.
        """

        password = 'ABC123!'
        user = self.create_and_login_user(password=password)

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        new_password = 'DEF456?'
        data = self.post(f'/user/reset-password/{token}', data=dict(
            password=new_password,
            password_confirmation=new_password
        ))

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

        password = 'ABC123!'
        user = self.create_user(email='jane@doe.com', name='Jane Doe', password=password)

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        new_password = 'DEF456?'
        data = self.post(f'/user/reset-password/{token}', data=dict(
            password=new_password,
            password_confirmation=new_password
        ))

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

        password = 'ABC123!'
        user = self.create_user(email='jane@doe.com', name='Jane Doe', password=password)

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        new_password = 'DEF456?'
        data = self.post(f'/user/reset-password/{token}', data=dict(
            password=new_password,
            password_confirmation=new_password + 'GHI'
        ))

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

        password = 'ABC123!'
        user = self.create_user(email='jane@doe.com', name='Jane Doe', password=password)

        new_password = 'DEF456?'
        data = self.post('/user/reset-password/just-some-token', expected_status=404, data=dict(
            password=new_password,
            password_confirmation=new_password
        ))

        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    def test_reset_password_post_failure_no_user(self):
        """
            Test posting to the password reset form with an anonymous user, a token for a non-existing user, and a valid
            form.

            Expected result: The password is not updated and the user is shown a 404 error page.
        """

        password = 'ABC123!'
        user = self.create_user(email='jane@doe.com', name='Jane Doe', password=password)

        token_obj = ResetPasswordToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        db.session.delete(user)
        db.session.commit()

        new_password = 'DEF456?'
        data = self.post(f'/user/reset-password/{token}', expected_status=404, data=dict(
            password=new_password,
            password_confirmation=new_password + 'GHI'
        ))

        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    # endregion
