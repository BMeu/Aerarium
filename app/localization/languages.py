#!venv/bin/python
# -*- coding: utf-8 -*-

from os import listdir
import re
from typing import Iterable

from flask import current_app
from flask import request

"""
    Helpers regarding language functionality.
"""


def get_languages(translation_dir: str, default_language: str = 'en') -> Iterable[str]:
    """
        Get a list of available languages.

        The default language is (generic) English and will always be included. All other languages will be read from
        the folder ``translation_dir``. A folder within that directory is considered to contain a language for the
        application if its name is either two lowercase letters, or two lowercase letters, a dash, and two uppercase
        letters.

        :Example:

        The following list contains *valid* language codes:

        * ``de``
        * ``de-DE``
        * ``de-AT``
        * ``de-CH``

        :Example:

        The following list contains *invalid* language codes:

        * ``EN``
        * ``EN-us``
        * ``EN-US``
        * ``en-us``
        * ``en-USA``

        :param default_language: The default language as used in the GetText functions within the code (defaults to
            ``en``).
        :param translation_dir: The directory within which the GetText translation folders can be found.
        :return: A list of language codes supported by the application.
    """

    # Get a list of all entries in the translations folder and filter it. If the given folder could not be read, do not
    # include any additional languages.
    pattern = re.compile('^([a-z]{2})(-[A-Z]{2})?$')
    try:
        languages = [language for language in listdir(translation_dir) if pattern.match(language)]
    except OSError:
        languages = []

    return [default_language] + languages


def get_locale() -> str:
    """
        Get the language most suitable to the user's settings.

        :return: The chosen language code.
    """

    # TODO: Set from user settings, accept header, global settings.
    locale = request.accept_languages.best_match(current_app.config['LANGUAGES'])
    return locale
