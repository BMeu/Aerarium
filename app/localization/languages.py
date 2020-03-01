# -*- coding: utf-8 -*-

"""
    Helpers regarding language functionality.
"""

from typing import Iterable
from typing import Optional
from typing import Tuple

from os import listdir
import re

from flask import current_app
from flask import request
from flask_babel import get_locale as get_current_locale
from flask_babel import Locale
from flask_login import current_user


def get_default_language() -> str:
    """
        Get the application's default language.

        :return: The language code of the default language.
    """

    return 'en'


def get_language_names(translation_dir: str, with_native_names: bool = True) -> Iterable[Tuple[str, str]]:
    """
        Get a list of languages supported by the application, each with their name in the current language

        :param translation_dir: The directory within which the GetText translation folders can be found.
        :param with_native_names: If set to `True`, the languages' names will not only be given in the current language,
                                  but also in their native language.
        :return: A list of tuples, with the first element being the language code and the second one being the
                 language's name.
    """

    # The language in which the application is currently running.
    current_locale = get_current_locale()
    current_language = current_locale.language

    names = []
    languages = get_languages(translation_dir, get_default_language())
    for language in languages:
        # Get the locale for the currently looked at language.
        locale = Locale(language)

        # Get the language's name in the current language.
        name = locale.get_display_name(current_language)

        # If native names are requested, and the current language is not the one we are currently looking at,
        # determine the native name.
        if with_native_names and language != current_language:
            native_name = locale.get_display_name(language)

            name = f'{name} ({native_name})'

        names.append((language, name))

    # Sort the list of language names by their name, i.e. the second element in the tuple.
    names.sort(key=lambda x: x[1])
    return names


def get_languages(translation_dir: str, default_language: Optional[str] = None) -> Iterable[str]:
    """
        Get a list of available languages.

        The default language is (generic) English and will always be included. All other languages will be read from
        the folder `translation_dir`. A folder within that directory is considered to contain a language for the
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

        :param default_language: The default language as used in the GetText functions within the code. If not given,
                                 the default language from :meth:`get_default_language` will be used.
        :param translation_dir: The directory within which the translation folders can be found.
        :return: A list of language codes supported by the application.
    """

    if not default_language:
        default_language = get_default_language()

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
        Get the language most suitable to the user's preferences.

        :return: The chosen language code.
    """

    # Get the language from the user if they are logged in.
    if current_user and not current_user.is_anonymous and current_user.settings.language:
        return current_user.settings.language  # type: ignore

    # Choose the best matching language from the request headers.
    locale = request.accept_languages.best_match(current_app.config['LANGUAGES'])
    return locale  # type: ignore
