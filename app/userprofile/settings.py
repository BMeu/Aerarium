#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The application's model for user settings.
"""

from app import db


class UserSettings(db.Model):
    """
        A collection of settings each user can individually define.
    """

    _user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
    """
        The ID of the user to which this setting instance belongs. The actual user object can be accessed via the
        attribute `user`.
    """
