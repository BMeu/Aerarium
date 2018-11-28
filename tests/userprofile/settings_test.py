#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.localization import get_default_language
from app.userprofile import User
from app.userprofile import UserSettings


class UserSettingsTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
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

    def test_db_relationship(self):
        """
            Test that the user is directly accessible from their respective settings.

            Expected result: The user has a settings object that directly links back to the user.
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertIsNotNone(user.settings)
        self.assertIsNotNone(user.settings.user)
        self.assertEqual(user.id, user.settings._user_id)
        self.assertEqual(user, user.settings.user)

        # Load the settings directly from the DB.
        settings = UserSettings.query.get(user.id)

        self.assertIsNotNone(settings)
        self.assertEqual(user, settings.user)

    def test_init_defaults(self):
        """
            Test initializing a settings object with default values.

            Expected result: The setting's default values are set.
        """

        settings = UserSettings()
        settings._user_id = 1
        db.session.add(settings)
        db.session.commit()

        # The language is initialized with the default language.
        self.assertEqual(get_default_language(), settings._language)

    def test_language_get(self):
        """
            Test getting the language.

            Expected result: The language is returned.
        """
        language = 'de'
        settings = UserSettings(_language=language)
        self.assertEqual(language, settings._language)
        self.assertEqual(settings._language, settings.language)

    def test_language_set_success(self):
        """
            Test setting a valid language.

            Expected result: The language is correctly set.
        """

        language = 'de'
        settings = UserSettings()
        self.assertNotEqual(language, settings.language)

        settings.language = language
        self.assertEqual(language, settings.language)

    def test_language_set_failure(self):
        """
            Test setting n invalid language.

            Expected result: The language is not set, instead an error is raised.
        """

        settings = UserSettings()
        language = settings.language

        invalid_language = 'not-a-language'
        self.assertNotEqual(invalid_language, settings.language)

        with self.assertRaises(ValueError) as exception_cm:
            settings.language = invalid_language

            self.assertEqual(language, settings.language)
            self.assertEqual(f'Invalid language "{invalid_language}"', str(exception_cm.exception))
