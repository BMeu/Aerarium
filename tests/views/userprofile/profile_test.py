#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app import mail
from app.configuration import TestConfiguration
from app.userprofile import User
from app.userprofile.tokens import ChangeEmailAddressToken


class ProfileTest(TestCase):

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

    # region Profile [GET]

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

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        with mail.record_messages() as outgoing:
            response = self.client.get('/user/profile', follow_redirects=True)
            data = response.get_data(as_text=True)

            self.assertEqual(0, len(outgoing))

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertNotIn('Your changes have been saved.', data)
            self.assertNotIn('An email has been sent to the new address', data)

    # endregion

    # region Profile [POST]

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

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_name = 'Jane Doe'
        with mail.record_messages() as outgoing:
            response = self.client.post('/user/profile', follow_redirects=True, data=dict(
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
        user.set_password(password + '!')
        with mail.record_messages() as outgoing:
            user.set_password(password)
            self.assertEqual(1, len(outgoing))
            self.assertIn('Your Password Has Been Changed', outgoing[0].subject)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_name = 'Jane Doe'
        new_password = '654321'
        with mail.record_messages() as outgoing:
            response = self.client.post('/user/profile', follow_redirects=True, data=dict(
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
        user.set_password(password + '!')
        with mail.record_messages() as outgoing:
            user.set_password(password)
            self.assertEqual(1, len(outgoing))
            self.assertIn('Your Password Has Been Changed', outgoing[0].subject)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_name = 'Jane Doe'
        new_password = '654321'
        new_email = 'test2@example.com'
        with mail.record_messages() as outgoing:
            response = self.client.post('/user/profile', follow_redirects=True, data=dict(
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

    # endregion

    # region Change Email

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
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user_id
        token_obj.new_email = new_email
        token = token_obj.create()

        response = self.client.get(f'/user/change-email-address/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        user = User.load_from_id(user_id)

        self.assertIn('Your email address has successfully been changed.', data)
        self.assertEqual(new_email, user.get_email())

    def test_change_email_failure_invalid_token(self):
        """
            Test accessing the change email page with an invalid token.

            Expected result: The email address is not changed and a 404 error page is shown.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        user_id = user.id
        new_email = 'test2@example.com'
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user_id
        token_obj.new_email = new_email
        token = token_obj.create()

        response = self.client.get(f'/user/change-email-address/invalid-{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        user = User.load_from_id(user_id)

        self.assertEqual(404, response.status_code)
        self.assertNotIn('Your email address has successfully been changed.', data)
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
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user_id
        token_obj.new_email = existing_email
        token = token_obj.create()

        response = self.client.get(f'/user/change-email-address/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        user = User.load_from_id(user_id)

        self.assertIn('The email address already is in use.', data)
        self.assertEqual(email, user.get_email())

    def test_change_email_failure_no_user(self):
        """
            Test accessing the change email page with a invalid token for a non-existing user.

            Expected result: The email address is not changed and a 404 error page is shown.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        user_id = user.id
        new_email = 'test2@example.com'
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user_id
        token_obj.new_email = new_email
        token = token_obj.create()

        db.session.delete(user)
        db.session.commit()

        response = self.client.get(f'/user/change-email-address/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertEqual(404, response.status_code)
        self.assertNotIn('Your email address has successfully been changed.', data)

    # endregion
