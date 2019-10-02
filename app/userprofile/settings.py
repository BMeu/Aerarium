#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The application's model for user settings.
"""

from app import db
from app.configuration import BaseConfiguration
from app.localization import get_default_language
from app.localization import get_languages


class UserSettings(db.Model):  # type: ignore
    """
        A collection of settings each user can individually define.
    """

    _user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
    """
        The ID of the user to which this setting instance belongs. The actual user object can be accessed via the
        attribute :attr:`user`.
    """

    _language = db.Column('language', db.String(5), default=get_default_language())
    """
        The language in which the user will see the application. Use :attr:`language` to access it.
    """

    @property
    def language(self) -> str:
        """
            The language in which the user will see the application.

            :return: The code of the user's language.
            :raise ValueError: If the assigned language is not supported by the application.
        """
        return self._language  # type: ignore

    @language.setter
    def language(self, value: str) -> None:
        """
            Set the user's language.

            :param value: The new language.
            :raise ValueError: If the new language is not supported by the application.
        """
        languages = get_languages(BaseConfiguration.TRANSLATION_DIR, get_default_language())
        if value not in languages:
            raise ValueError(f'Invalid language "{value}".')

        self._language = value
        return

    def reset(self) -> None:
        """
            Reset the settings to their default values.
        """

        for setting, column in self.__class__.__table__.columns.items():
            is_key = column.primary_key or len(column.foreign_keys) > 0
            if is_key:
                # Do not reset the keys, otherwise the object will be disassociated.
                continue

            # Reset to the default value. If there is no default column, reset to None.
            if column.default is not None:
                setattr(self, setting, column.default.execute(bind=db.engine))
            else:  # pragma: nocover
                # TODO: Currently there are no columns without a default value.
                #       Remove the nocover statement once a column without a default value is added.
                setattr(self, setting, None)
