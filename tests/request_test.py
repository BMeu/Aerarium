#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from flask import g
from flask import Response

from app import create_app
from app.configuration import TestConfiguration
from app.request import register_after_request_handlers
from app.request import register_before_request_handlers
# noinspection PyProtectedMember
from app.request import _extend_global_variable
# noinspection PyProtectedMember
from app.request import _header_x_clacks_overhead


class RequestTest(TestCase):

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

    @patch('app.request.Flask')
    def test_register_after_request_handlers(self, mock_app: MagicMock):
        """
            Test the after-request handler registration.

            Expected result: The handlers are registered against the application
        """
        app_instance = mock_app.return_value
        app_instance.after_request = MagicMock()

        register_after_request_handlers(app_instance)

        app_instance.after_request.assert_called_with(_header_x_clacks_overhead)

    def test_header_x_clacks_overhead(self):
        """
            Test the X-Clacks-Overhead header.

            Expected result: The response header is extended with the X-Clacks-Overhead field, but otherwise unchanged.
        """
        response = Response()
        response.headers = MagicMock()
        response.headers.add = MagicMock()

        extended_response = _header_x_clacks_overhead(response)

        response.headers.add.assert_called_once_with('X-Clacks-Overhead', 'GNU Terry Pratchett')
        self.assertEqual(response, extended_response)

    @patch('app.request.Flask')
    def test_register_before_request_handlers(self, mock_app: MagicMock):
        """
            Test the before-request handler registration.

            Expected result: The handlers are registered against the application
        """
        app_instance = mock_app.return_value
        app_instance.before_request = MagicMock()

        register_before_request_handlers(app_instance)

        app_instance.before_request.assert_called_with(_extend_global_variable)

    @patch('app.request.get_locale')
    def test_extend_global_variable(self, mock_get_locale: MagicMock):
        """
            Test the extended global variable.

            Expected result: The response header is extended with the X-Clacks-Overhead field, but otherwise unchanged.
        """
        mock_get_locale.return_value = 'en-DE'

        _extend_global_variable()

        self.assertEqual(g.locale, 'en-DE')
