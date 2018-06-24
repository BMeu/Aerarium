#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app.configuration import TestConfiguration


class RoutesTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """
            Reset the test cases.
        """
        self.app_context.pop()

    def test_index_default(self):
        """
            Test the dashboard without a given username.

            Expected result: The dashboard header is shown, but no greeting.
        """
        response = self.client.get('/')
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertNotIn('Welcome, ', data)

    def test_index_with_username(self):
        """
            Test the dashboard with a given username.

            Expected result: The response contains a greeting specific to the given user.
        """
        response = self.client.get('/Bastian')
        data = response.get_data(as_text=True)

        self.assertIn('Dashboard', data)
        self.assertIn('Welcome, Bastian!', data)
