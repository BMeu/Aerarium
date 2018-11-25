#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from app import create_app
from app import Email
from app import mail
from app.configuration import TestConfiguration
from app.exceptions import NoMailSenderError


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

    def test_init_with_sender(self):
        """
            Test initializing an email object with a given sender.

            Expected result: The object is correctly initialized.
        """
        subject = 'Test Subject'
        body_path = 'email/test'
        sender = 'test@example.com'
        email = Email(subject, body_path, sender)

        self.assertEqual(subject, email._subject)
        self.assertEqual(body_path, email._body_template_base_path)
        self.assertIsNone(email._body_plain)
        self.assertIsNone(email._body_html)
        self.assertEqual(sender, email._sender)

    def test_init_without_sender(self):
        """
            Test initializing an email object without a given sender.

            Expected result: The object is correctly initialized; the sender is taken from the app configuration.
        """
        mail_from = self.app.config['MAIL_FROM']
        self.app.config['MAIL_FROM'] = 'test@example.com'

        subject = 'Test Subject'
        body_path = 'email/test'
        email = Email(subject, body_path)

        self.assertEqual(subject, email._subject)
        self.assertEqual(body_path, email._body_template_base_path)
        self.assertIsNone(email._body_plain)
        self.assertIsNone(email._body_html)
        self.assertEqual(self.app.config['MAIL_FROM'], email._sender)

        self.app.config['MAIL_FROM'] = mail_from

    def test_init_without_sender_and_configuration(self):
        """
            Test initializing an email object without a sender if the sender is not specified in the configuration.

            Expected result: The object is not initialized and raises an error.
        """
        mail_from = self.app.config['MAIL_FROM']
        self.app.config['MAIL_FROM'] = None

        subject = 'Test Subject'
        body_path = 'email/test'

        with self.assertRaises(NoMailSenderError) as exception_cm:
            email = Email(subject, body_path)

            self.assertIsNone(email)
            self.assertIn('No sender given and none configured in the app configuration.', str(exception_cm.exception))

        self.app.config['MAIL_FROM'] = mail_from

    @patch('app.email.render_template')
    def test_prepare(self, mock_renderer: MagicMock):
        """
            Test preparing the email body.

            Expected result: The previously set body is rendered with the given arguments.
        """

        def _renderer_side_effect(template, **_kwargs):
            """
                Return the template path for testing.
            """
            return template

        mock_renderer.side_effect = _renderer_side_effect

        subject = 'Test Subject'
        body_path = 'email/test'
        sender = 'test@example.com'
        email = Email(subject, body_path, sender)

        title = 'Test Title'
        body_path_plain = body_path + '.txt'
        body_path_html = body_path + '.html'
        email.prepare(title=title)

        self.assertEqual(body_path_plain, email._body_plain)
        self.assertEqual(body_path_html, email._body_html)
        self.assertEqual(2, mock_renderer.call_count)
        self.assertTupleEqual(call(body_path_plain, title=title), mock_renderer.call_args_list[0])
        self.assertTupleEqual(call(body_path_html, title=title), mock_renderer.call_args_list[1])

    def test_prepare_and_send(self):
        """
            Test preparing and sending a mail with a single call.

            Expected result: The two respective methods are called.
        """

        subject = 'Test Subject'
        body_path = 'email/test'
        sender = 'test@example.com'
        email = Email(subject, body_path, sender)

        email.prepare = Mock()
        email.send = Mock()

        title = 'Test Title'
        recipient = 'mail@example.com'
        email.prepare_and_send(recipient, title=title)

        # noinspection PyUnresolvedReferences
        self.assertEqual(1, email.prepare.call_count)

        # noinspection PyUnresolvedReferences
        self.assertTupleEqual(call(title=title), email.prepare.call_args)

        # noinspection PyUnresolvedReferences
        self.assertEqual(1, email.send.call_count)

        # noinspection PyUnresolvedReferences
        self.assertTupleEqual(call(recipient), email.send.call_args)

    def test_send_success_single_recipient(self):
        """
            Test sending an email to a single recipient.

            Expected result: The email is sent successfully.
        """

        subject = 'Test Subject'
        body_path = 'email/test'
        sender = 'test@example.com'
        recipient = 'mail@example.com'
        body_plain = 'Plain Body'
        body_html = 'HTML Body'

        email = Email(subject, body_path, sender)
        email._body_plain = body_plain
        email._body_html = body_html

        with mail.record_messages() as outgoing:
            email.send(recipient)

            self.assertEqual(1, len(outgoing))
            self.assertEqual(subject, outgoing[0].subject)
            self.assertEqual(sender, outgoing[0].sender)
            self.assertListEqual([recipient], outgoing[0].recipients)
            self.assertEqual(body_plain, outgoing[0].body)
            self.assertEqual(body_html, outgoing[0].html)

    def test_send_success_multiple_recipients(self):
        """
            Test sending an email to multiple recipients.

            Expected result: The email is sent successfully.
        """

        subject = 'Test Subject'
        body_path = 'email/test'
        sender = 'test@example.com'
        recipients = ['mail@example.com', 'info@example.com']
        body_plain = 'Plain Body'
        body_html = 'HTML Body'

        email = Email(subject, body_path, sender)
        email._body_plain = body_plain
        email._body_html = body_html

        with mail.record_messages() as outgoing:
            email.send(recipients)

            self.assertEqual(1, len(outgoing))
            self.assertEqual(subject, outgoing[0].subject)
            self.assertEqual(sender, outgoing[0].sender)
            self.assertListEqual(recipients, outgoing[0].recipients)
            self.assertEqual(body_plain, outgoing[0].body)
            self.assertEqual(body_html, outgoing[0].html)

    def test_send_failure(self):
        """
            Test sending an email to a recipient given in a wrong type.

            Expected result: The email is not sent.
        """

        subject = 'Test Subject'
        body_path = 'email/test'
        sender = 'test@example.com'
        recipients = None
        body_plain = 'Plain Body'
        body_html = 'HTML Body'

        email = Email(subject, body_path, sender)
        email._body_plain = body_plain
        email._body_html = body_html

        with self.assertRaises(TypeError) as message:
            with mail.record_messages() as outgoing:
                # noinspection PyTypeChecker
                email.send(recipients)

                self.assertEqual(0, len(outgoing))
                self.assertEqual('Argument "recipients" must be a string or a list of strings.', message)
