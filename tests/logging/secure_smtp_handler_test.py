#!venv/bin/python
# -*- coding: utf-8 -*-

from logging import DEBUG
from logging import LogRecord
from logging.handlers import SMTPHandler
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from app.logging import SecureSMTPHandler


class SecureSMTPHandlerTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.settings = {
            'mailhost': ('smtp.example.com', 465),
            'fromaddr': 'no-reply@example.com',
            'toaddrs': ['mail@example.com', 'info@example.com'],
            'subject': 'Just Testing',
            'credentials': ('user', 'pwd'),
            'secure': (),
            'timeout': 4.2,
        }

        self.handler = SecureSMTPHandler(**self.settings)
        self.handler_ssl = SecureSMTPHandler(ssl=True, **self.settings)

        self.log_record = LogRecord('Log Record', DEBUG, '.', 42, 'This is a debug message.', None, None)

    def test_init(self):
        """
            Test correct initialization of the handlers.

            Expected result: Both handlers are equal except for the `ssl` field. Both are equal to the standard
            SMTP handler (except for the `ssl field`.
        """

        # Check the handler (without SSL) for correct initialization.
        self.assertEqual('smtp.example.com', self.handler.mailhost)
        self.assertEqual(465, self.handler.mailport)
        self.assertEqual('user', self.handler.username)
        self.assertEqual('pwd', self.handler.password)
        self.assertEqual('no-reply@example.com', self.handler.fromaddr)
        self.assertListEqual(['mail@example.com', 'info@example.com'], self.handler.toaddrs)
        self.assertEqual('Just Testing', self.handler.subject)
        self.assertTupleEqual((), self.handler.secure)
        self.assertEqual(4.2, self.handler.timeout)
        self.assertFalse(self.handler.ssl)

        # Check for correct initialization by comparing to a standard SMTP handler.
        std_handler = SMTPHandler(**self.settings)
        self.assertEqual(std_handler.mailhost, self.handler.mailhost)
        self.assertEqual(std_handler.mailport, self.handler.mailport)
        self.assertEqual(std_handler.username, self.handler.username)
        self.assertEqual(std_handler.password, self.handler.password)
        self.assertEqual(std_handler.fromaddr, self.handler.fromaddr)
        self.assertListEqual(std_handler.toaddrs, self.handler.toaddrs)
        self.assertEqual(std_handler.subject, self.handler.subject)
        self.assertTupleEqual(std_handler.secure, self.handler.secure)
        self.assertEqual(std_handler.timeout, self.handler.timeout)

        # Check the handler (with SSL) for correct initialization by comparing to the handler without SSL.
        self.assertEqual(self.handler.mailhost, self.handler_ssl.mailhost)
        self.assertEqual(self.handler.mailport, self.handler_ssl.mailport)
        self.assertEqual(self.handler.username, self.handler_ssl.username)
        self.assertEqual(self.handler.password, self.handler_ssl.password)
        self.assertEqual(self.handler.fromaddr, self.handler_ssl.fromaddr)
        self.assertListEqual(self.handler.toaddrs, self.handler_ssl.toaddrs)
        self.assertEqual(self.handler.subject, self.handler_ssl.subject)
        self.assertTupleEqual(self.handler.secure, self.handler_ssl.secure)
        self.assertEqual(self.handler.timeout, self.handler_ssl.timeout)
        self.assertTrue(self.handler_ssl.ssl)

    @patch('app.logging.secure_smtp_handler.SMTP')
    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit(self, mock_smtp_ssl: MagicMock, mock_smtp: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler (without SSL).

            Expected result: The record is sent without errors using SMTP.
        """

        # Set up the mock object.
        instance = mock_smtp.return_value
        instance.starttls.return_value = True
        instance.login.return_value = True
        instance.send_message.return_value = True

        self.handler.emit(self.log_record)

        mock_smtp.assert_called_once_with('smtp.example.com', 465, timeout=4.2)
        mock_smtp_ssl.assert_not_called()

        instance.starttls.assert_called()
        instance.login.assert_called_once_with('user', 'pwd')
        instance.send_message.assert_called_once()

    @patch('app.logging.secure_smtp_handler.SMTP')
    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit_ssl(self, mock_smtp_ssl: MagicMock, mock_smtp: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler.

            Expected result: The record is sent without errors using SMTP_SSL.
        """

        # Set up the mock object.
        instance = mock_smtp_ssl.return_value
        instance.starttls.return_value = True
        instance.login.return_value = True
        instance.send_message.return_value = True

        mock_smtp_ssl.starttls = MagicMock()

        self.handler_ssl.emit(self.log_record)

        mock_smtp_ssl.assert_called_once_with('smtp.example.com', 465, timeout=4.2)
        mock_smtp.assert_not_called()

        instance.starttls.assert_called()
        instance.login.assert_called_once_with('user', 'pwd')
        instance.send_message.assert_called_once()

    @patch('app.logging.secure_smtp_handler.SMTP')
    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit_ssl_defaults(self, mock_smtp_ssl: MagicMock, mock_smtp: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler without a port and TLS.

            Expected result: The record is sent without errors using SMTP_SSL.
        """

        # Set up the mock object.
        instance = mock_smtp_ssl.return_value
        instance.starttls.return_value = True
        instance.login.return_value = True
        instance.send_message.return_value = True

        self.handler_ssl.mailport = None
        self.handler_ssl.secure = None

        self.handler_ssl.emit(self.log_record)

        mock_smtp_ssl.assert_called_once_with('smtp.example.com', 465, timeout=4.2)
        mock_smtp.assert_not_called()

        instance.starttls.assert_not_called()
        instance.login.assert_called_once_with('user', 'pwd')
        instance.send_message.assert_called_once()

    @patch('app.logging.secure_smtp_handler.SMTP')
    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit_ssl_no_authenticating(self, mock_smtp_ssl: MagicMock, mock_smtp: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler without authentication.

            Expected result: The record is sent without errors using SMTP_SSL.
        """

        # Set up the mock object.
        instance = mock_smtp_ssl.return_value
        instance.starttls.return_value = True
        instance.login.return_value = True
        instance.send_message.return_value = True

        self.handler_ssl.username = None
        self.handler_ssl.secure = None

        self.handler_ssl.emit(self.log_record)

        mock_smtp_ssl.assert_called_once_with('smtp.example.com', 465, timeout=4.2)
        mock_smtp.assert_not_called()

        instance.starttls.assert_not_called()
        instance.login.assert_not_called()
        instance.send_message.assert_called_once()

    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit_ssl_raise_keyboard_interrupt(self, mock_smtp_ssl: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler, emitting a KeyboardInterrupt.

            Expected result: The record is not send, and the KeyboardInterrupt is reraised.
        """

        # Set up the mock object.
        instance = mock_smtp_ssl.return_value
        instance.send_message.side_effect = KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.handler_ssl.emit(self.log_record)

        instance.send_message.assert_called_once()

    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit_ssl_raise_system_exit(self, mock_smtp_ssl: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler, emitting a SystemExit.

            Expected result: The record is not send, and the SystemExit is reraised.
        """

        # Set up the mock object.
        instance = mock_smtp_ssl.return_value
        instance.send_message.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            self.handler_ssl.emit(self.log_record)

        instance.send_message.assert_called_once()

    @patch('app.logging.secure_smtp_handler.SMTP_SSL')
    def test_emit_ssl_not_raise_exception(self, mock_smtp_ssl: MagicMock):
        """
            Run the `emit(record)` method for the SSL handler, emitting an exception that is handled directly.

            Expected result: The record is not send, and no exception is raised.
        """

        # Set up the mock object.
        instance = mock_smtp_ssl.return_value
        instance.send_message.side_effect = Exception
        self.handler_ssl.handleError = MagicMock()

        self.handler_ssl.emit(self.log_record)

        instance.send_message.assert_called_once()
        self.handler_ssl.handleError.assert_called_once_with(self.log_record)
