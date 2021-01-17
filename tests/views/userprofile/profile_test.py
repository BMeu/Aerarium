# -*- coding: utf-8 -*-

from app import db
from app import mail
from app.userprofile import User
from app.userprofile.tokens import ChangeEmailAddressToken
from tests.views import ViewTestCase


class ProfileTest(ViewTestCase):

    # region Profile [GET]

    def test_user_profile_get(self):
        """
            Test accessing the user profile page.

            Expected result: The form is shown with prepopulated data.
        """

        email = 'test@example.com'
        name = 'John Doe'
        self.create_and_login_user(email=email, name=name)

        with mail.record_messages() as outgoing:
            data = self.get('/user/profile')

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
        user = self.create_and_login_user(email=email, name=name, password=password)

        new_name = 'Jane Doe'
        with mail.record_messages() as outgoing:
            data = self.post('/user/profile', data=dict(
                name=new_name,
                email=email
            ))

            self.assertEqual(0, len(outgoing))

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{new_name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertIn('Your changes have been saved.', data)
            self.assertNotIn('An email has been sent to the new address', data)

            user = User.load_from_id(user.id)
            self.assertEqual(new_name, user.name)
            self.assertEqual(email, user.email)
            self.assertTrue(user.check_password(password))

    def test_user_profile_post_name_and_password(self):
        """
            Test posting to the user profile page with the name and the password changed.

            Expected result: The form is shown with the new data. The user's name and password are changed, everything
                             else is not.
        """

        email = 'test@example.com'
        name = 'John Doe'
        password = 'ABC123!'
        user = self.create_and_login_user(email=email, name=name, password=password)

        new_name = 'Jane Doe'
        new_password = '654321'
        with mail.record_messages() as outgoing:
            data = self.post('/user/profile', data=dict(
                name=new_name,
                email=email,
                password=new_password,
                password_confirmation=new_password
            ))

            self.assertEqual(1, len(outgoing))

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{new_name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertIn('Your changes have been saved.', data)
            self.assertNotIn('An email has been sent to the new address', data)

            user = User.load_from_id(user.id)
            self.assertEqual(new_name, user.name)
            self.assertEqual(email, user.email)
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
        user = self.create_and_login_user(email=email, name=name, password=password)

        new_name = 'Jane Doe'
        new_password = '654321'
        new_email = 'test2@example.com'
        with mail.record_messages() as outgoing:
            data = self.post('/user/profile', data=dict(
                name=new_name,
                email=new_email,
                password=new_password,
                password_confirmation=new_password
            ))

            self.assertEqual(2, len(outgoing))
            self.assertIn('Change Your Email Address', outgoing[1].subject)
            self.assertEqual([new_email], outgoing[1].recipients)

            self.assertIn('User Profile', data)
            self.assertIn(f'value="{new_name}"', data)
            self.assertIn(f'value="{email}"', data)
            self.assertIn('Your changes have been saved.', data)
            self.assertIn('An email has been sent to the new address', data)

            user = User.load_from_id(user.id)
            self.assertEqual(new_name, user.name)
            self.assertEqual(email, user.email)
            self.assertTrue(user.check_password(new_password))

    # endregion

    # region Change Email

    def test_change_email_success(self):
        """
            Test accessing the change email page with a valid token.

            Expected result: The email address is changed.
        """

        user = self.create_user(email='test@example.com', name='John Doe', password='ABC123!')

        new_email = 'test2@example.com'
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user.id
        token_obj.new_email = new_email
        token = token_obj.create()

        data = self.get(f'/user/change-email-address/{token}')

        user = User.load_from_id(user.id)

        self.assertIn('Your email address has successfully been changed.', data)
        self.assertEqual(new_email, user.email)

    def test_change_email_failure_invalid_token(self):
        """
            Test accessing the change email page with an invalid token.

            Expected result: The email address is not changed and a 404 error page is shown.
        """

        email = 'test@example.com'
        user = self.create_user(email=email, name='John Doe', password='ABC123!')

        new_email = 'test2@example.com'
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user.id
        token_obj.new_email = new_email
        token = token_obj.create()

        data = self.get(f'/user/change-email-address/invalid-{token}', expected_status=404)

        user = User.load_from_id(user.id)

        self.assertNotIn('Your email address has successfully been changed.', data)
        self.assertEqual(email, user.email)

    def test_change_email_failure_email_in_use(self):
        """
            Test accessing the change email page with an email address that already is in use by another user.

            Expected result: The email address is not changed.
        """

        existing_email = 'test2@example.com'
        existing_name = 'Jane Doe'
        self.create_user(email=existing_email, name=existing_name, password='ABC123!')

        email = 'test@example.com'
        name = 'John Doe'
        user = self.create_user(email=email, name=name, password='!321CBA')

        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user.id
        token_obj.new_email = existing_email
        token = token_obj.create()

        data = self.get(f'/user/change-email-address/{token}')

        user = User.load_from_id(user.id)

        self.assertIn('The email address already is in use.', data)
        self.assertEqual(email, user.email)

    def test_change_email_failure_no_user(self):
        """
            Test accessing the change email page with a valid token for a non-existing user.

            Expected result: The email address is not changed and a 404 error page is shown.
        """

        user = self.create_user(email='test@example.com', name='John Doe', password='ABC123!')

        new_email = 'test2@example.com'
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user.id
        token_obj.new_email = new_email
        token = token_obj.create()

        db.session.delete(user)
        db.session.commit()

        data = self.get(f'/user/change-email-address/{token}', expected_status=404)

        self.assertNotIn('Your email address has successfully been changed.', data)

    # endregion
