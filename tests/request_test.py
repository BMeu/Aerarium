#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from flask import Response

from app.request import register_after_request_handlers
# noinspection PyProtectedMember
from app.request import _header_x_clacks_overhead


class RequestTest(TestCase):

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
