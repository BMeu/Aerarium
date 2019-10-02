#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app import get_app
from app.configuration import TestConfiguration
from app.exceptions import NoApplicationError


class ApplicationTest(TestCase):

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

    def test_get_app_success(self):
        """
            Test getting the current application object.

            Expected result: The application object is successfully returned.
        """
        app = get_app()
        self.assertIsNotNone(app)

    def test_get_app_failure(self):
        """
            Test getting the current application object outside the application context.

            Expected result: ``None`` is returned without an exception.
        """

        # Remove the application context.
        self.app_context.pop()

        with self.assertRaises(NoApplicationError):
            app = get_app()
            self.assertIsNone(app)

        # Re-add the application context so the tear-down method will not pop an empty list.
        self.app_context.push()
