#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The application's model for user settings.
"""

from app import db
from app.configuration import BaseConfiguration
from app.localization import get_default_language
from app.localization import get_languages


class UserSettings(db.Model):
    """
        A collection of settings each user can individually define.
    """

    _user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
    """
        The ID of the user to which this setting instance belongs. The actual user object can be accessed via the
        attribute `user`.
    """

    _language = db.Column('language', db.String(5), default=get_default_language())
    """
        The language in which the user will see the application. Use :attr:`.language` to access it.
    """

    @property
    def language(self) -> str:
        """
            Get the user's language.

            :return: The code of the user's language.
        """
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        """
            Set the user's language.

            :param value: The new language.
            :raise :
        """
        languages = get_languages(BaseConfiguration.TRANSLATION_DIR, get_default_language())
        if value not in languages:
            raise ValueError(f'Invalid language "{value}".')

        self._language = value
        return
