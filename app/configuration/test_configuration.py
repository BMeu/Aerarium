#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    A configuration specialized for testing the application.
"""

from app.configuration import BaseConfiguration


class TestConfiguration(BaseConfiguration):
    """
        A specialized configuration for testing the application.
    """

    TESTING: bool = True

    # Set to minimum number of rounds to minimize testing time.
    BCRYPT_LOG_ROUNDS: int = 4

    SECRET_KEY: str = 'testing-Aerarium'

    LANGUAGES = ['en', 'de', 'en-US']

    # Use an in-memory SQLite database to avoid stale files.
    SQLALCHEMY_DATABASE_URI: str = 'sqlite://'

    # Disable CSRF protection to easily test from submissions.
    WTF_CSRF_ENABLED: bool = False
