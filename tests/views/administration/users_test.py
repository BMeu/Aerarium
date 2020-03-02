# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import patch

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User
from app.views.administration.forms import UserSettingsResetForm


class UsersTest(TestCase):

    # region Test Setup

    def setUp(self):
        """
            Prepare the test cases.
        """

        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

        # Create a role for accessing the user administration.
        self.role = Role('Administrator')
        self.role.permissions = Permission.EditUser
        db.session.add(self.role)
        db.session.commit()

    def tearDown(self):
        """
            Clean up after each test case.
        """

        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def create_and_login_test_user(self) -> User:
        """
            Create a test user and log them in.

            :return: The created user.
        """

        email = 'doe@example.com'
        password = 'ABC123!'
        user = User(email, 'Jane Doe')
        user.set_password(password)
        user.role = self.role
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password,
        ))

        return user

    @staticmethod
    def validate_on_submit_failure():
        """
            A mock method for validating forms that will always fail.

            :return: `False`
        """

        return False

    # endregion

    def test_users_list(self):
        """
            Test the list of all users.

            Expected Result: All users that fit on the requested page are displayed, sorted by their name.
        """

        self.app.config['ITEMS_PER_PAGE'] = 2

        # Add users, but not sorted by name.
        user_john = User('john@example.com', 'John')
        db.session.add(user_john)

        # Use this user to access the page.
        email = 'johanna@example.com'
        password = 'ABC123!'
        user_johanna = User(email, 'Johanna')
        user_johanna.set_password(password)
        user_johanna.role = self.role
        db.session.add(user_johanna)

        user_jona = User('jona@example.com', 'Jona')
        db.session.add(user_jona)
        db.session.commit()

        users_assorted = [
            user_john,
            user_johanna,
            user_jona,
        ]

        # Ensure that they are not sorted by name on the DB.
        users = User.query.all()
        self.assertListEqual(users_assorted, users)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('administration/users', follow_redirects=True)
        data = response.get_data(as_text=True)

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

        user = self.create_and_login_test_user()

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        response = self.client.get(f'/administration/user/{non_existing_user_id}', follow_redirects=True)
        self.assertEqual(404, response.status_code)

    def test_user_header_get_existing_user(self):
        """
            Test editing a user.

            Expected result: The edit page is shown.
        """

        user = self.create_and_login_test_user()

        response = self.client.get(f'/administration/user/{user.id}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn(f'Edit User “{user.name}”', data)
        self.assertIn(f'Edit the user\'s header data.', data)
        self.assertNotIn(f'Edit the user\'s settings.', data)

    def test_user_header_post_no_user(self):
        """
            Test editing a user that does not exist.

            Expected result: An error 404 is returned.
        """

        user = self.create_and_login_test_user()

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        response = self.client.post(f'/administration/user/{non_existing_user_id}', follow_redirects=True, data=dict())
        self.assertEqual(404, response.status_code)

    def test_user_header_post_existing_user(self):
        """
            Test editing a user.

            Expected result: The edit page is shown.
        """

        user = self.create_and_login_test_user()

        response = self.client.post(f'/administration/user/{user.id}', follow_redirects=True, data=dict())
        data = response.get_data(as_text=True)

        self.assertIn(f'Edit User “{user.name}”', data)
        self.assertIn(f'Edit the user\'s header data.', data)
        self.assertNotIn(f'Edit the user\'s settings.', data)

    def test_user_settings_get_no_user(self):
        """
            Test editing user settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        user = self.create_and_login_test_user()

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        response = self.client.get(f'/administration/user/{non_existing_user_id}/settings', follow_redirects=True)
        self.assertEqual(404, response.status_code)

    def test_user_settings_get_existing_user(self):
        """
            Test editing user settings for an existing user.

            Expected result: The user's settings are displayed.
        """

        user = self.create_and_login_test_user()

        response = self.client.get(f'/administration/user/{user.id}/settings', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)

        # Ensure that the user's current language is preselected in the form.
        self.assertIn(f'<option selected value="{user.settings.language}">', data)

    def test_user_settings_post_no_user(self):
        """
            Test editing user settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        user = self.create_and_login_test_user()

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        response = self.client.post(f'/administration/user/{non_existing_user_id}/settings',
                                    follow_redirects=True,
                                    data=dict())
        self.assertEqual(404, response.status_code)

    def test_user_settings_post_existing_user(self):
        """
            Test editing user settings for an existing user.

            Expected result: The user's settings are changed and the new settings are displayed.
        """

        user = self.create_and_login_test_user()

        new_language = 'de'
        response = self.client.post(f'/administration/user/{user.id}/settings', follow_redirects=True, data=dict(
            language=new_language,
        ))
        data = response.get_data(as_text=True)

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

        user = self.create_and_login_test_user()

        response = self.client.get(f'/administration/user/{user.id}/settings/reset', follow_redirects=True)
        self.assertEqual(405, response.status_code)

    def test_user_settings_reset_post_no_user(self):
        """
            Test resetting user settings for a user that does not exist.

            Expected result: An error 404 is returned.
        """

        user = self.create_and_login_test_user()

        non_existing_user_id = user.id + 1
        self.assertIsNone(User.load_from_id(non_existing_user_id))

        response = self.client.post(f'/administration/user/{non_existing_user_id}/settings/reset',
                                    follow_redirects=True,
                                    data=dict())
        self.assertEqual(404, response.status_code)

    def test_user_settings_reset_post_success(self):
        """
            Test resetting some user's settings.

            Expected result: The settings are reset.
        """

        language = 'de'
        user = self.create_and_login_test_user()
        user.settings.language = language
        db.session.commit()

        self.assertEqual(language, user.settings.language)

        response = self.client.post(f'/administration/user/{user.id}/settings/reset',
                                    follow_redirects=True,
                                    data=dict())
        data = response.get_data(as_text=True)

        self.assertIn('The settings have been set to their default values.', data)
        self.assertEqual('en', user.settings.language)

    @patch.object(UserSettingsResetForm, 'validate_on_submit', validate_on_submit_failure)
    def test_user_settings_reset_post_failure(self):
        """
            Test resetting some user's with an invalid form..

            Expected result: The settings are reset.
        """

        language = 'de'
        user = self.create_and_login_test_user()
        user.settings.language = language
        db.session.commit()

        self.assertEqual(language, user.settings.language)

        response = self.client.post(f'/administration/user/{user.id}/settings/reset',
                                    follow_redirects=True,
                                    data=dict())
        data = response.get_data(as_text=True)

        self.assertNotIn('The settings have been set to their default values.', data)
        self.assertEqual(language, user.settings.language)
