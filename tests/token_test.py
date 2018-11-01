#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.token import get_token
from app.token import get_validity
from app.token import verify_token


class TokenTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_validity_success_seconds(self):
        """
            Test getting the validity in seconds.

            Expected result: The validity as defined in the configuration is returned.
        """

        # Validity: 600 seconds.
        validity = 600
        self.app.config['TOKEN_VALIDITY'] = validity

        self.assertEqual(validity, get_validity())

    def test_get_validity_success_minutes(self):
        """
            Test getting the validity in minutes.

            Expected result: The validity as defined in the configuration is returned, but in minutes.
        """

        # Validity: 10 minutes.
        validity = 10
        self.app.config['TOKEN_VALIDITY'] = validity * 60

        self.assertEqual(validity, get_validity(in_minutes=True))

    def test_get_validity_success_minutes_rounded(self):
        """
            Test getting the validity in minutes, but with a value that needs to be rounded.

            Expected result: The validity as defined in the configuration is returned, but in minutes and rounded down
                             to the nearest integer.
        """

        # Validity: 90 seconds
        validity = 90
        self.app.config['TOKEN_VALIDITY'] = validity

        self.assertEqual(1, get_validity(in_minutes=True))

    def test_get_validity_failure(self):
        """
            Test getting the validity outside the application context.

            Expected result: No validity is returned.
        """

        # Remove the application context.
        self.app_context.pop()

        validity = get_validity()
        self.assertIsNone(validity)

        # Re-add the application context so the tear-down method will not pop an empty list.
        self.app_context.push()

    def test_get_token_success(self):
        """
            Test getting a token with some payload.

            Expected result: A token is returned. The token is of type ``str``
        """
        token = get_token(user_id=1, name='John Doe', email='test@example.com')
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

    def test_get_token_success_no_payload(self):
        """
            Test getting a token without some payload.

            Expected result: A token is returned.
        """
        token = get_token()
        self.assertIsNotNone(token)

    def test_get_token_failure(self):
        """
            Test getting a token outside the application context.

            Expected result: No token is returned.
        """

        # Remove the application context.
        self.app_context.pop()

        token = get_token(user_id=1, name='John Doe', email='test@example.com')
        self.assertIsNone(token)

        # Re-add the application context so the tear-down method will not pop an empty list.
        self.app_context.push()

    def test_verify_token_success(self):
        """
            Test verifying a valid token.

            Expected result: The input payload is returned, without an expiration field.
        """
        token = get_token(user_id=1, name='John Doe', email='test@example.com')
        payload = verify_token(token)
        self.assertDictEqual(dict(
            email='test@example.com',
            name='John Doe',
            user_id=1
        ), payload)

    def test_verify_token_failure_outside_app(self):
        """
            Test verifying a valid token outside the application context.

            Expected result: ``None`` is returned.
        """
        token = get_token(user_id=1, name='John Doe', email='test@example.com')

        # Remove the application context.
        self.app_context.pop()

        payload = verify_token(token)
        self.assertIsNone(payload)

        # Re-add the application context so the tear-down method will not pop an empty list.
        self.app_context.push()

    def test_verify_token_failure_invalid_input(self):
        """
            Test verifying a token that is not a string.

            Expected result: ``None`` is returned.
        """
        # noinspection PyTypeChecker
        payload = verify_token(123456789)
        self.assertIsNone(payload)

    def test_verify_token_failure_manipulated_token(self):
        """
            Test verifying a token that has been manipulated.

            Expected result: ``None`` is returned.
        """
        token = get_token(user_id=1, name='John Doe', email='test@example.com')
        payload = verify_token(token + 'BMeuWasHere')
        self.assertIsNone(payload)

    def test_verify_token_failure_expired(self):
        """
            Test verifying a token that is expired.

            Expected result: ``None`` is returned.
        """
        self.app.config['TOKEN_VALIDITY'] = -10

        token = get_token(user_id=1, name='John Doe', email='test@example.com')
        payload = verify_token(token)
        self.assertIsNone(payload)
