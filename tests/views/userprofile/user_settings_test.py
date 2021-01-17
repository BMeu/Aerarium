# -*- coding: utf-8 -*-

from unittest.mock import patch

from app import db
from app.views.userprofile.forms import UserSettingsResetForm
from tests.views import ViewTestCase


class UserSettingsTest(ViewTestCase):

    def test_user_settings_get(self):
        """
            Test getting the user settings.

            Expected result: The form is shown with prepopulated data.
        """

        user = self.create_and_login_user()

        data = self.get('/user/settings')

        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)

        # Ensure that the user's current language is preselected in the form.
        self.assertIn(f'<option selected value="{user.settings.language}">', data)

    def test_user_settings_post(self):
        """
            Test posting to the user settings page.

            Expected result: The form is shown with the new data, the language is updated.
        """

        user = self.create_and_login_user()

        self.assertEqual('en', user.settings.language)

        new_language = 'de'
        data = self.post('/user/settings', data=dict(
            language=new_language,
        ))

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

        user = self.create_and_login_user()

        language = 'de'
        user.settings.language = language

        db.session.commit()

        self.assertEqual(language, user.settings.language)

        data = self.post('/user/settings/reset')

        self.assertIn('The settings have been set to their default values.', data)
        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)
        self.assertEqual('en', user.settings.language)

    @patch.object(UserSettingsResetForm, 'validate_on_submit', ViewTestCase.get_false)
    def test_user_settings_reset_failure(self):
        """
            Test resetting the user settings via accessing the page with an invalid form.

            Expected result: The user settings are not reset to their default values.
        """

        user = self.create_and_login_user()

        language = 'de'
        user.settings.language = language

        db.session.commit()

        self.assertEqual(language, user.settings.language)

        data = self.post('/user/settings/reset')

        self.assertNotIn('The settings have been set to their default values.', data)
        self.assertIn('Einstellungen', data)
        self.assertNotIn('Your changes have been saved.', data)
        self.assertEqual(language, user.settings.language)
