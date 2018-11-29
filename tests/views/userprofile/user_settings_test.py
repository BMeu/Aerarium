#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import patch

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import User
from app.views.userprofile.forms import UserSettingsResetForm


class UserSettingsTest(TestCase):

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

    @staticmethod
    def validate_on_submit():
        """
            A mock method for validating forms that will always fail.

            :return: `False`
        """
        return False

    def test_user_settings_get(self):
        """
            Test getting the user settings.

            Expected result: The form is shown with prepopulated data.
        """
        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/settings', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)

        # Ensure that the user's current language is preselected in the form.
        self.assertIn(f'<option selected value="{user.settings.language}">', data)

    def test_user_settings_post(self):
        """
            Test posting to the user settings page.

            Expected result: The form is shown with the new data, the language is updated.
        """
        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        self.assertEqual('en', user.settings.language)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        new_language = 'de'
        response = self.client.post('/user/settings', follow_redirects=True, data=dict(
            language=new_language,
        ))
        data = response.get_data(as_text=True)

        self.assertNotIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)
        self.assertIn('Einstellungen', data)
        self.assertIn('Deine Änderungen wurden gespeichert.', data)

        self.assertEqual(new_language, user.settings.language)

    def test_user_settings_reset_success(self):
        """
            Test resetting the user settings via accessing the page.

            Expected result: The user settings are reset to their default values.
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)

        language = 'de'
        user.settings.language = language

        db.session.commit()

        self.assertEqual(language, user.settings.language)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post('/user/settings/reset', follow_redirects=True, data=dict())
        data = response.get_data(as_text=True)

        self.assertIn('The settings have been set to their default values.', data)
        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)
        self.assertEqual('en', user.settings.language)

    @patch.object(UserSettingsResetForm, 'validate_on_submit', validate_on_submit)
    def test_user_settings_reset_failure(self):
        """
            Test resetting the user settings via accessing the page with an invalid form.

            Expected result: The user settings are not reset to their default values.
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)

        language = 'de'
        user.settings.language = language

        db.session.commit()

        self.assertEqual(language, user.settings.language)

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post('/user/settings/reset', follow_redirects=True, data=dict())
        data = response.get_data(as_text=True)

        self.assertNotIn('The settings have been set to their default values.', data)
        self.assertIn('Einstellungen', data)
        self.assertNotIn('Your changes have been saved.', data)
        self.assertEqual(language, user.settings.language)
