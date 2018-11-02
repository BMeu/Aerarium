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

    # region User Profile

    def test_user_profile_get(self):
        """
            Test accessing the user profile page.

            Expected result: The form is shown with prepopulated data.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        with mail.record_messages() as outgoing:
            response = self.client.get('/user', follow_redirects=True)
            data = response.get_data(as_text=True)

            self.assertEqual(0, len(outgoing))

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertNotIn('Your changes have been saved.', data)
            self.assertNotIn('An email has been sent to the new address', data)

    def test_user_profile_post_only_name(self):
        """
            Test posting to the user profile page with only the name changed.

            Expected result: The form is shown with the new data. The user's name is changed, everything else is not.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_name = 'Jane Doe'
        with mail.record_messages() as outgoing:
            response = self.client.post('/user', follow_redirects=True, data=dict(
                name=new_name,
                email=email
            ))
            data = response.get_data(as_text=True)

            self.assertEqual(0, len(outgoing))

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{new_name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertIn('Your changes have been saved.', data)
            self.assertNotIn('An email has been sent to the new address', data)

            user = User.load_from_id(user_id)
            self.assertEqual(new_name, user.name)
            self.assertEqual(email, user.get_email())
            self.assertTrue(user.check_password(password))

    def test_user_profile_post_name_and_password(self):
        """
            Test posting to the user profile page with the name and the password changed.

            Expected result: The form is shown with the new data. The user's name and password are changed, everything
                             else is not.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = '123456'
        user = User(email, name)
        with mail.record_messages() as outgoing:
            user.set_password(password)
            self.assertEqual(1, len(outgoing))
            self.assertIn('Your Password Has Been Changed', outgoing[0].subject)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_name = 'Jane Doe'
        new_password = '654321'
        with mail.record_messages() as outgoing:
            response = self.client.post('/user', follow_redirects=True, data=dict(
                name=new_name,
                email=email,
                password=new_password,
                password_confirmation=new_password
            ))
            data = response.get_data(as_text=True)

            self.assertEqual(1, len(outgoing))

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{new_name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertIn('Your changes have been saved.', data)
            self.assertNotIn('An email has been sent to the new address', data)

            user = User.load_from_id(user_id)
            self.assertEqual(new_name, user.name)
            self.assertEqual(email, user.get_email())
            self.assertTrue(user.check_password(new_password))
            self.assertIn('Your changes have been saved.', data)

    def test_user_profile_post_name_and_password_and_email(self):
        """
            Test posting to the user profile page with the name, the password, and the email changed.

            Expected result: The form is shown with the new data. The user's name and password are changed, the email
                             is not, but a mail has been sent to the new address.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = '123456'
        user = User(email, name)
        with mail.record_messages() as outgoing:
            user.set_password(password)
            self.assertEqual(1, len(outgoing))
            self.assertIn('Your Password Has Been Changed', outgoing[0].subject)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_name = 'Jane Doe'
        new_password = '654321'
        new_email = 'test2@example.com'
        with mail.record_messages() as outgoing:
            response = self.client.post('/user', follow_redirects=True, data=dict(
                name=new_name,
                email=new_email,
                password=new_password,
                password_confirmation=new_password
            ))
            data = response.get_data(as_text=True)

            self.assertEqual(2, len(outgoing))
            self.assertIn('Change Your Email Address', outgoing[1].subject)
            self.assertEqual([new_email], outgoing[1].recipients)

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{new_name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertIn('Your changes have been saved.', data)
            self.assertIn('An email has been sent to the new address', data)

            user = User.load_from_id(user_id)
            self.assertEqual(new_name, user.name)
            self.assertEqual(email, user.get_email())
            self.assertTrue(user.check_password(new_password))
            self.assertIn('Your changes have been saved.', data)

    def test_change_email_success(self):
        """
            Test accessing the change email page with a valid token.

            Expected result: The email address is changed.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        user_id = user.id
        new_email = 'test2@example.com'
        token = user._get_change_email_address_token(new_email)
        self.assertIsNotNone(token)

        response = self.client.get(f'/user/change-email/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        user = User.load_from_id(user_id)

        self.assertIn('Your email address has successfully been changed.', data)
        self.assertEqual(new_email, user.get_email())

    def test_change_email_failure_invalid_token(self):
        """
            Test accessing the change email page with an invalid token.

            Expected result: The email address is not changed.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        user_id = user.id
        new_email = 'test2@example.com'
        token = user._get_change_email_address_token(new_email)
        self.assertIsNotNone(token)

        response = self.client.get(f'/user/change-email/invalid-{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        user = User.load_from_id(user_id)

        self.assertIn('The token is invalid.', data)
        self.assertEqual(email, user.get_email())

    def test_change_email_failure_email_in_use(self):
        """
            Test accessing the change email page with an email address that already is in use by another user.

            Expected result: The email address is not changed.
        """
        existing_email = 'test2@example.com'
        existing_name = 'Jane Doe'
        existing_user = User(existing_email, existing_name)

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(existing_user)
        db.session.add(user)
        db.session.commit()

        user_id = user.id
        token = user._get_change_email_address_token(existing_email)
        self.assertIsNotNone(token)

        response = self.client.get(f'/user/change-email/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        user = User.load_from_id(user_id)

        self.assertIn('The email address already is in use.', data)
        self.assertEqual(email, user.get_email())

    # endregion

    # region Password Reset

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

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        response = self.client.get(f'/reset-password/{token}', follow_redirects=True)
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

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        response = self.client.get(f'/reset-password/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Reset Your Password', data)
        self.assertIn('New Password', data)
        self.assertNotIn('The token is invalid.', data)
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
        self.assertIn('The token is invalid.', data)
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

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        new_password = 'abcdef'
        response = self.client.post(f'/reset-password/{token}', follow_redirects=True, data=dict(
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

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        new_password = 'abcdef'
        response = self.client.post(f'/reset-password/{token}', follow_redirects=True, data=dict(
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

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        new_password = 'abcdef'
        response = self.client.post(f'/reset-password/{token}', follow_redirects=True, data=dict(
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
        self.assertIn('The token is invalid.', data)
        self.assertNotIn('Reset Your Password', data)
        self.assertNotIn('Your password has successfully been changed.', data)
        self.assertFalse(user.check_password(new_password))
        self.assertTrue(user.check_password(password))

    # endregion

    # region Login/Logout

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

    # endregion
