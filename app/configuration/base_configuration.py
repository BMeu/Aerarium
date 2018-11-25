#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    A base configuration that loads settings from environment variables and sets appropriate defaults for all
    configuration variables used in the application.
"""

from typing import Iterable
from typing import Optional

from os import environ
from os import path

# noinspection PyPackageRequirements
from dotenv import load_dotenv

from app.localization import get_languages

# These basic directories have to be set outside the configuration class so the .env file is loaded before the class.
_basedir = path.abspath(path.dirname(path.dirname(path.dirname(__file__))))
_instance_dir = path.join(_basedir, 'instance')

# Load the user configuration from the .env file.
load_dotenv(path.join(_instance_dir, '.env'))


class BaseConfiguration:
    """
        Configuration for the application. Where useful, settings are read from environment variables; default values
        are set.
    """

    # Directories used by the application.
    BASE_DIR: str = _basedir
    INSTANCE_DIR: str = _instance_dir
    LOG_DIR: str = environ.get('LOG_DIR', path.join(INSTANCE_DIR, 'logs'))
    TMP_DIR: str = environ.get('TMP_DIR', path.join(INSTANCE_DIR, 'tmp'))
    TRANSLATION_DIR: str = path.join(BASE_DIR, 'app', 'translations')

    # General application settings.
    LANGUAGES: Iterable[str] = get_languages(TRANSLATION_DIR)
    SYS_ADMINS: Optional[Iterable[str]] = [mail for mail in str.split(environ.get('SYS_ADMINS'), ';')] \
        if environ.get('SYS_ADMINS') else None
    SUPPORT_ADDRESS: Optional[str] = environ.get('SUPPORT_ADDRESS', None)

    # Security settings.
    BCRYPT_HANDLE_LONG_PASSWORDS: int = 1
    BCRYPT_LOG_ROUNDS: int = int(environ.get('BCRYPT_LOG_ROUNDS', 12))
    SECRET_KEY: str = environ.get('SECRET_KEY')
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = True if environ.get('USE_HTTP', '0') != '1' else False
    PREFERRED_URL_SCHEME: str = 'https' if environ.get('USE_HTTP', '0') != '1' else 'http'
    TOKEN_VALIDITY: int = int(environ.get('TOKEN_VALIDITY', 900))

    # Database settings.
    SQLALCHEMY_DATABASE_URI: str = environ.get('DATABASE_URI', 'sqlite:///' + path.join(_instance_dir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Mail settings.
    MAIL_SERVER: str = environ.get('MAIL_SERVER')
    MAIL_PORT: int = int(environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS: bool = environ.get('MAIL_USE_TLS', '0') == '1'
    MAIL_USE_SSL: bool = environ.get('MAIL_USE_SSL', '0') == '1'
    MAIL_USERNAME: str = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD: str = environ.get('MAIL_PASSWORD')
    MAIL_FROM: Optional[str] = environ.get('MAIL_FROM',
                                           ('no-reply@' + MAIL_SERVER) if MAIL_SERVER is not None else None)

    # Logging settings (the log directory is defined above).
    LOG_TO_STDOUT: bool = environ.get('LOG_TO_STDOUT', '0') == '1'
    LOG_MAX_FILES: int = int(environ.get('LOG_MAX_FILES', 10))
    LOG_FILE_MAX_KB: int = int(environ.get('LOG_FILE_MAX_KB', 10))

    # App name (short and long form) for easy and consistent usage across the entire application.
    TITLE_SHORT = 'Aerarium'
    TITLE_LONG = 'Aerarium: Managing Your Finances'
