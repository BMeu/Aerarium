#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.views.authorization.tokens import ChangeEmailAddressToken
from app.views.authorization.tokens import DeleteAccountToken
from app.views.authorization.tokens import ResetPasswordToken
from app.configuration import TestConfiguration


class ChangeEmailAddressTokenTest(TestCase):

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

    def test_init(self):
        """
            Test initializing a change email address token.

            Expected result: The token is initialized with emtpy values.
        """
        token = ChangeEmailAddressToken()
        self.assertIsNotNone(token)
        self.assertIsNone(token.user_id)
        self.assertIsNone(token.new_email)


class DeleteAccountTokenTest(TestCase):

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

    def test_init(self):
        """
            Test initializing a delete account token.

            Expected result: The token is initialized with emtpy values.
        """
        token = DeleteAccountToken()
        self.assertIsNotNone(token)
        self.assertIsNone(token.user_id)


class ResetPasswordTokenTest(TestCase):

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

    def test_init(self):
        """
            Test initializing a password reset token.

            Expected result: The token is initialized with emtpy values.
        """
        token = ResetPasswordToken()
        self.assertIsNotNone(token)
        self.assertIsNone(token.user_id)
