#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from app import create_app
from app.configuration import TestConfiguration
from app.localization import get_languages
from app.localization import get_locale


class LanguagesTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()

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
        self.app_context.pop()

    @patch('app.localization.languages.listdir')
    def test_get_languages_default(self, mock_listdir: MagicMock):
        """
            Run the `get_languages()` function with the default language.

            Expected result: A list containing the default `'en'` plus the valid languages from `listdir()`.
        """
        mock_listdir.return_value = self.listdir_return_value

        languages = get_languages(self.path)

        mock_listdir.assert_called_with(self.path)
        self.assertListEqual([self.default_language, 'de', 'en-US'], languages)

    @patch('app.localization.languages.listdir')
    def test_get_languages_non_default(self, mock_listdir: MagicMock):
        """
            Run the `get_languages()` function with a non-default language.

            Expected result: A list containing the non-default language plus the valid languages from `listdir()`.
        """
        mock_listdir.return_value = self.listdir_return_value

        languages = get_languages(self.path, 'fr')

        mock_listdir.assert_called_with(self.path)
        self.assertListEqual(['fr', 'de', 'en-US'], languages)

    @patch('app.localization.languages.listdir')
    def test_get_languages_nonexistent_path(self, mock_listdir: MagicMock):
        """
            Run the get_languages() function with a non-existent path (and default language).

            Expected result: A list simply containing the default language, no errors.
        """
        mock_listdir.side_effect = OSError

        languages = get_languages(self.path)

        self.assertListEqual([self.default_language], languages)

    @patch('app.localization.languages.request')
    def test_get_locale(self, mock_request: MagicMock):
        """
            Run the get_locale() function with best_match() returning 'de'.

            Expected result: 'de'.
        """
        mock_request.accept_languages = MagicMock()
        mock_request.accept_languages.best_match = MagicMock(return_value='de')

        language = get_locale()
        self.assertEqual('de', language)
