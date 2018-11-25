#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from flask import url_for
from flask_login import login_user
from werkzeug.wrappers import Response

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import logout_required
from app.userprofile import User


class DecoratorsTest(TestCase):

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

    def test_logout_required_logged_out(self):
        """
            Test the ``logout_required`` decorator with an anonymous user.

            Expected result: The decorated view function is returned.
        """

        def test_view_function() -> str:
            """
                A simple test "view" function.

                :return: 'Decorated View'.
            """
            return 'Decorated View'

        view_function = logout_required(test_view_function)
        response = view_function()
        self.assertEqual('Decorated View', response)

    def test_logout_required_logged_in(self):
        """
            Test the ``logout_required`` decorator with a logged-in user.

            Expected result: The redirect response to the home page is returned.
        """

        def test_view_function() -> str:
            """
                A simple test "view" function.

                :return: 'Decorated View'.
            """
            return 'Decorated View'

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()
        login_user(user)

        redirect_function = logout_required(test_view_function)
        response = redirect_function()
        self.assertIsInstance(response, Response)
        self.assertEqual(302, response.status_code)
        self.assertEqual(url_for('main.index'), response.location)
