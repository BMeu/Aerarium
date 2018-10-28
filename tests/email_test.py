#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import mail
from app import send_email
from app.configuration import TestConfiguration


class EmailTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """
            Reset the test cases.
        """
        self.app_context.pop()

    def test_send_email_success(self):
        """
            Test sending an email.

            Expected result: The email would have been sent if it weren't in test mode.
        """
        subject = 'Test Subject'
        sender = 'no-reply@example.com'
        recipients = ['test@example.com']
        body_plain = 'Plain-text body.'
        body_html = '<html><head><title>Test Email</title></head><body><h1>HTML body.</h1></body></html>'

        with mail.record_messages() as outgoing:
            send_email(subject, sender, recipients, body_plain, body_html)

            self.assertEqual(1, len(outgoing))
            self.assertEqual(subject, outgoing[0].subject)
            self.assertEqual(sender, outgoing[0].sender)
            self.assertEqual(recipients, outgoing[0].recipients)
            self.assertEqual(body_plain, outgoing[0].body)
            self.assertEqual(body_html, outgoing[0].html)

    def test_send_email_failure(self):
        """
            Test sending an email outside the application context.

            Expected result: No email would have been sent.
        """

        # Remove the application context.
        self.app_context.pop()

        subject = 'Test Subject'
        sender = 'no-reply@example.com'
        recipients = ['test@example.com']
        body_plain = 'Plain-text body.'
        body_html = '<html><head><title>Test Email</title></head><body><h1>HTML body.</h1></body></html>'

        with mail.record_messages() as outgoing:
            send_email(subject, sender, recipients, body_plain, body_html)

            self.assertEqual(0, len(outgoing))

        # Re-add the application context so the tear-down method will not pop an empty list.
        self.app_context.push()
