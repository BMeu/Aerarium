#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.authorization import User
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
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.push()
        self.app_context.pop()

    def test_index_logged_out(self):
        """
            Test the dashboard without an anonymous user.

            Expected result: The user is redirected to the login page.
        """
        response = self.client.get('/', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertNotIn('<h1>Dashboard</h1>', data)
        self.assertIn('<h1>Log In</h1>', data)

    def test_index_logged_in(self):
        """
            Test accessing the dashboard with a logged in user.

            Expected result: The user is shown the dashboard.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('<h1>Dashboard</h1>', data)
        self.assertNotIn('<h1>Log In</h1>', data)
