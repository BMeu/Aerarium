# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.views.tools import get_next_page


class ToolsTest(TestCase):

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

    def test_get_next_page_default_param(self):
        """
            Test getting the next page with default arguments if the next page is given.

            Expected result: The next page given in the request arguments.
        """

        next_arg = '/user/profile'
        self.request_context.request.args = {'next': next_arg, 'n': next_arg + '/delete'}
        next_page = get_next_page()
        self.assertEqual(next_arg, next_page)

    def test_get_next_page_other_param(self):
        """
            Test getting the next page if the next page is given in a different URL parameter.

            Expected result: The next page given in the request arguments.
        """

        param = 'n'
        next_arg = '/user/profile'
        self.request_context.request.args = {'next': next_arg + '/delete', param: next_arg}
        next_page = get_next_page(url_param=param)
        self.assertEqual(next_arg, next_page)

    def test_get_next_page_default_fallback(self):
        """
            Test getting the next page with default arguments if no next page is given.

            Expected result: The default fallback URL.
        """

        fallback = '/'
        next_page = get_next_page()
        self.assertEqual(fallback, next_page)

    def test_get_next_page_other_fallback(self):
        """
            Test getting the next page with default arguments if no next page is given.

            Expected result: The default fallback URL.
        """

        fallback = '/user/logout'
        next_page = get_next_page(fallback_url=fallback)
        self.assertEqual(fallback, next_page)

    def test_get_next_page_invalid_url(self):
        """
            Test getting the next page with default arguments if no next page is given.

            Expected result: The default fallback URL.
        """

        fallback = '/'
        self.request_context.request.args = {'next': 'https://www.example.com'}
        next_page = get_next_page()
        self.assertEqual(fallback, next_page)
