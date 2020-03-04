# -*- coding: utf-8 -*-

from unittest.mock import patch

from app import db
from app import mail
from app.userprofile import Permission
from app.userprofile import User
from app.views.administration.forms import UserPasswordResetForm
from app.views.administration.forms import UserSettingsResetForm
from tests.views import ViewTestCase


class UsersTest(ViewTestCase):

    def test_users_list(self):
        """
            Test the list of all users.

            Expected Result: All users that fit on the requested page are displayed, sorted by their name.
        """

        self.app.config['ITEMS_PER_PAGE'] = 2

        role = self.create_role(Permission.EditUser)

        # Add users, but not sorted by name.
        user_john = self.create_user(email='john@example.com', name='John', password='ABC123!')
        user_johanna = self.create_and_login_user(email='johanna@example.com', name='Johanna', role=role)
        user_jona = self.create_user(email='jona@example.com', name='Jona', password='ABC123!')

        users_assorted = [
            user_john,
            user_johanna,
            user_jona,
        ]

        # Ensure that they are not sorted by name on the DB.
        users = User.query.all()
        self.assertListEqual(users_assorted, users)

        data = self.get('administration/users')

        title_user_john = f'Edit user “{user_john.name}”'
        title_user_johanna = f'Edit user “{user_johanna.name}”'
        title_user_jona = f'Edit user “{user_jona.name}”'

        self.assertIn('Users', data)
        self.assertIn(title_user_john, data)
        self.assertIn(title_user_johanna, data)
        self.assertNotIn(title_user_jona, data)
        self.assertIn('Displaying users 1 to 2 of 3', data)

        # Test that the order of the John and Johanna users match.
        pos_of_johanna = data.find(title_user_johanna)
        pos_of_john = data.find(title_user_john)
        self.assertLess(pos_of_johanna, pos_of_john)

    def test_user_header_get_no_user(self):
        """
            Test editing a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.get(f'/administration/user/{non_existing_user_id}', expected_status=404)

    def test_user_header_get_existing_user(self):
        """
            Test editing a user.

            Expected result: The edit page is shown.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        data = self.get(f'/administration/user/{user.id}')

        self.assertIn(f'Edit User “{user.name}”', data)
        self.assertIn(f'Edit the user\'s header data.', data)
        self.assertNotIn(f'Edit the user\'s settings.', data)

    def test_user_header_post_no_user(self):
        """
            Test editing a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.post(f'/administration/user/{non_existing_user_id}', expected_status=404)

    def test_user_header_post_existing_user(self):
        """
            Test editing a user.

            Expected result: The edit page is shown.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        data = self.post(f'/administration/user/{user.id}')

        self.assertIn(f'Edit User “{user.name}”', data)
        self.assertIn(f'Edit the user\'s header data.', data)
        self.assertNotIn(f'Edit the user\'s settings.', data)

    def test_user_security_no_user(self):
        """
            Test viewing the security settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.get(f'/administration/user/{non_existing_user_id}/security', expected_status=404)

    def test_user_security_existing_user(self):
        """
            Test viewing the security settings for an existing user.

            Expected result: The security settings are displayed.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        data = self.get(f'/administration/user/{user.id}/security')

        self.assertIn('Edit the user\'s security settings.', data)
        self.assertIn('Reset Password', data)

    def test_user_password_reset_get(self):
        """
            Test resetting a user's password by accessing the URL directly.

            Expected result: An error 405 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        self.get(f'/administration/user/{user.id}/security/reset-password', expected_status=405)

    def test_user_password_reset_post_no_user(self):
        """
            Test resetting a user's password for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.post(f'/administration/user/{non_existing_user_id}/security/reset-password', expected_status=404)

    def test_user_password_reset_post_success(self):
        """
            Test resetting a user's password for an existing user.

            Expected result: The password reset mail is sent.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        with mail.record_messages() as outgoing:
            data = self.post(f'/administration/user/{user.id}/security/reset-password')

            self.assertIn('password has been reset. An email has been sent', data)
            self.assertEqual(1, len(outgoing))
            self.assertEqual([user.email], outgoing[0].recipients)

    @patch.object(UserPasswordResetForm, 'validate_on_submit', ViewTestCase.get_false)
    def test_user_password_reset_post_failure(self):
        """
            Test resetting a user's password with an invalid form.

            Expected result: The password reset mail is not sent.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        with mail.record_messages() as outgoing:
            data = self.post(f'/administration/user/{user.id}/security/reset-password')

            self.assertNotIn('password has been reset. An email has been sent', data)
            self.assertEqual(0, len(outgoing))

    def test_user_settings_get_no_user(self):
        """
            Test editing user settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.get(f'/administration/user/{non_existing_user_id}/settings', expected_status=404)

    def test_user_settings_get_existing_user(self):
        """
            Test editing user settings for an existing user.

            Expected result: The user's settings are displayed.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        data = self.get(f'/administration/user/{user.id}/settings')

        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)

        # Ensure that the user's current language is preselected in the form.
        self.assertIn(f'<option selected value="{user.settings.language}">', data)

    def test_user_settings_post_no_user(self):
        """
            Test editing user settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.post(f'/administration/user/{non_existing_user_id}/settings', expected_status=404)

    def test_user_settings_post_existing_user(self):
        """
            Test editing user settings for an existing user.

            Expected result: The user's settings are changed and the new settings are displayed.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        new_language = 'de'
        data = self.post(f'/administration/user/{user.id}/settings', data=dict(
            language=new_language,
        ))

        self.assertNotIn('Settings', data)
        self.assertIn('Einstellungen', data)
        self.assertNotIn('Your changes have been saved.', data)
        self.assertIn('Deine Änderungen wurden gespeichert.', data)

        self.assertEqual(new_language, user.settings.language)

        # Ensure that the user's current language is preselected in the form.
        self.assertIn(f'<option selected value="{user.settings.language}">', data)

    def test_user_settings_reset_get(self):
        """
            Test resetting user settings by accessing the URL directly.

            Expected result: An error 405 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        self.get(f'/administration/user/{user.id}/settings/reset', expected_status=405)

    def test_user_settings_reset_post_no_user(self):
        """
            Test resetting user settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        self.post(f'/administration/user/{non_existing_user_id}/settings/reset', expected_status=404)

    def test_user_settings_reset_post_success(self):
        """
            Test resetting some user's settings.

            Expected result: The settings are reset.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        language = 'de'
        user.settings.language = language
        db.session.commit()

        self.assertEqual(language, user.settings.language)

        data = self.post(f'/administration/user/{user.id}/settings/reset')

        self.assertIn('The settings have been set to their default values.', data)
        self.assertEqual('en', user.settings.language)

    @patch.object(UserSettingsResetForm, 'validate_on_submit', ViewTestCase.get_false)
    def test_user_settings_reset_post_failure(self):
        """
            Test resetting some user's with an invalid form..

            Expected result: The settings are not reset.
        """

        role = self.create_role(Permission.EditUser)
        user = self.create_and_login_user(role=role)

        language = 'de'
        user.settings.language = language
        db.session.commit()

        self.assertEqual(language, user.settings.language)

        data = self.post(f'/administration/user/{user.id}/settings/reset')

        self.assertNotIn('The settings have been set to their default values.', data)
        self.assertEqual(language, user.settings.language)
