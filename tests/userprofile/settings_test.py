#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
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
