# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from flask_babel import Locale

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.localization import get_default_language
from app.localization import get_language_names
from app.localization import get_languages
from app.localization import get_locale
from app.userprofile import User


class LanguagesTest(TestCase):

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

        self.default_language = 'en'
        self.path = 'mock/test'
        self.listdir_return_value = [
            'de',
            'en-US',
            'not-a-language',
            '12-34',
            'DE',
            'DE-de',
            'de-',
            'de--',
            'de--DE',
            'de-DEE',
            'de-AT-CH',
            '-DE',
            '-',
            '',
        ]

    def tearDown(self):
        """
            Reset the test cases.
        """

        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def test_get_default_language(self):
        """
            Test getting the default language.

            Expected result: 'en' is always returned.
        """

        self.assertEqual(self.default_language, get_default_language())

    @patch('app.localization.languages.listdir')
    def test_get_language_names_with_native_names_english(self, mock_listdir: MagicMock):
        """
            Test getting the list of language names with their native names (with 'en' as locale).

            Expected result: The list is returned and sorted by their name.
        """

        mock_listdir.return_value = [
            'es',
            'fr',
            'de',
        ]
        expected_names = [
            ('en', 'English'),
            ('fr', 'French (français)'),
            ('de', 'German (Deutsch)'),
            ('es', 'Spanish (español)'),
        ]

        names = get_language_names(TestConfiguration.TRANSLATION_DIR)
        mock_listdir.assert_called()
        self.assertListEqual(expected_names, list(names))

    @patch('app.localization.languages.get_current_locale')
    @patch('app.localization.languages.listdir')
    def test_get_language_names_with_native_names_german(self, mock_listdir: MagicMock,
                                                         mock_get_current_locale: MagicMock):
        """
            Test getting the list of language names with their native names (with 'de' as locale).

            Expected result: The list is returned and sorted by their name.
        """

        mock_get_current_locale.return_value = Locale('de')
        mock_listdir.return_value = [
            'es',
            'fr',
            'de',
        ]
        expected_names = [
            ('de', 'Deutsch'),
            ('en', 'Englisch (English)'),
            ('fr', 'Französisch (français)'),
            ('es', 'Spanisch (español)'),
        ]

        names = get_language_names(TestConfiguration.TRANSLATION_DIR)
        mock_listdir.assert_called()
        self.assertListEqual(expected_names, list(names))

    @patch('app.localization.languages.listdir')
    def test_get_language_names_without_native_names(self, mock_listdir: MagicMock):
        """
            Test getting the list of language names without their native names.

            Expected result: The list is returned and sorted by their name.
        """

        mock_listdir.return_value = [
            'es',
            'fr',
            'de',
        ]
        expected_names = [
            ('en', 'English'),
            ('fr', 'French'),
            ('de', 'German'),
            ('es', 'Spanish'),
        ]

        names = get_language_names(TestConfiguration.TRANSLATION_DIR, with_native_names=False)
        mock_listdir.assert_called()
        self.assertListEqual(expected_names, list(names))

    @patch('app.localization.languages.listdir')
    def test_get_languages_default(self, mock_listdir: MagicMock):
        """
            Run the `get_languages()` function with the default language.

            Expected result: A list containing the default `'en'` plus the valid languages from `listdir()`.
        """

        mock_listdir.return_value = self.listdir_return_value

        languages = get_languages(self.path)

        mock_listdir.assert_called_with(self.path)
        self.assertListEqual([self.default_language, 'de', 'en-US'], list(languages))

    @patch('app.localization.languages.listdir')
    def test_get_languages_non_default(self, mock_listdir: MagicMock):
        """
            Run the `get_languages()` function with a non-default language.

            Expected result: A list containing the non-default language plus the valid languages from `listdir()`.
        """

        mock_listdir.return_value = self.listdir_return_value

        languages = get_languages(self.path, 'fr')

        mock_listdir.assert_called_with(self.path)
        self.assertListEqual(['fr', 'de', 'en-US'], list(languages))

    @patch('app.localization.languages.listdir')
    def test_get_languages_nonexistent_path(self, mock_listdir: MagicMock):
        """
            Run the get_languages() function with a non-existent path (and default language).

            Expected result: A list simply containing the default language, no errors.
        """

        mock_listdir.side_effect = OSError

        languages = get_languages(self.path)

        self.assertListEqual([self.default_language], list(languages))

    @patch('app.localization.languages.request')
    def test_get_locale_from_user(self, mock_request: MagicMock):
        """
            Test getting the locale from a user who is logged in.

            Expected result: The user's preferred language is returned.
        """

        # Mock the best_match() function to ensure it is not called.
        mock_request.accept_languages = MagicMock()
        mock_request.accept_languages.best_match = MagicMock(return_value='de')

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        user.settings._language = 'fr'
        language = get_locale()
        self.assertEqual(user.settings._language, language)
        mock_request.accept_languages.best_match.assert_not_called()

    @patch('app.localization.languages.request')
    def test_get_locale_from_request(self, mock_request: MagicMock):
        """
            Test getting the locale if a user is not logged in.

            Expected result: 'de'.
        """

        mock_request.accept_languages = MagicMock()
        mock_request.accept_languages.best_match = MagicMock(return_value='de')

        language = get_locale()
        self.assertEqual('de', language)
