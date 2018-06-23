#!venv/bin/python
# -*- coding: utf-8 -*-

from logging import Formatter
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch
from sys import stdout

from app.logging import create_file_handler
from app.logging import create_mail_handler
from app.logging import create_stream_handler


class HandlerFactoryTest(TestCase):
    def setUp(self):
        """
            Initialize the test cases.
        """
        self.level = 42
        self.format = Formatter('%(message)s')

    @patch('app.logging.handler_factories.RotatingFileHandler')
    def test_create_file_handler(self, mock_handler: MagicMock):
        """
            Test the initialization of the file handler.

            Expected result: The file handler emits to the file on the correct level and with the correct formatter.
        """
        instance = mock_handler.return_value
        instance.setFormatter = MagicMock()
        instance.setLevel = MagicMock()

        file = 'mock/log/path/file.log'

        handler = create_file_handler(self.level, self.format, file, 2, 5)

        mock_handler.assert_called_with(file, maxBytes=2048, backupCount=5)
        instance.setFormatter.assert_called_with(self.format)
        instance.setLevel.assert_called_with(self.level)

        self.assertIsNotNone(handler)

    @patch('app.logging.handler_factories.SecureSMTPHandler')
    def test_create_mail_handler(self, mock_handler: MagicMock):
        """
            Test the initialization of the mail handler.

            Expected result: The mail handler sends via mail on the correct level and with the correct formatter.
        """
        instance = mock_handler.return_value
        instance.setFormatter = MagicMock()
        instance.setLevel = MagicMock()

        sender = 'no-reply@example.com'
        recipients = ['mail@example.com', 'test@example.com']
        subject = 'Aerarium Test'
        server = 'smtp.example.com'
        user = 'JSB'
        tls = True

        handler = create_mail_handler(self.level, self.format, sender, recipients, subject, server, user=user, tls=tls)

        mock_handler.assert_called_with((server, 25), sender, recipients, subject, (user, None), (), False)
        instance.setFormatter.assert_called_with(self.format)
        instance.setLevel.assert_called_with(self.level)

        self.assertIsNotNone(handler)

    @patch('app.logging.handler_factories.StreamHandler')
    def test_create_stream_handler(self, mock_handler: MagicMock):
        """
            Test the initialization of the stream handler.

            Expected result: The stream handler prints to STDOUT on the correct level and with the correct formatter.
        """
        instance = mock_handler.return_value
        instance.setFormatter = MagicMock()
        instance.setLevel = MagicMock()

        handler = create_stream_handler(self.level, self.format)

        mock_handler.assert_called_with(stdout)
        instance.setFormatter.assert_called_with(self.format)
        instance.setLevel.assert_called_with(self.level)

        self.assertIsNotNone(handler)
