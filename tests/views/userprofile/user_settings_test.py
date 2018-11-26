#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import User


class UserSettingsTest(TestCase):

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
        self.request_context.pop()
        self.app_context.pop()

    def test_user_settings_get(self):
        """
            Test getting the user settings.

            Expected result: The form is shown with prepopulated data.
        """
        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/user/settings', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn('Settings', data)
        self.assertNotIn('Your changes have been saved.', data)

    def test_user_settings_post(self):
        """
            Test posting to the user settings page.

            Expected result: The form is shown with the new data.
        """
        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post('/user/settings', follow_redirects=True, data=dict())
        data = response.get_data(as_text=True)

        self.assertIn('Settings', data)
        self.assertIn('Your changes have been saved.', data)
