#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app.configuration import TestConfiguration
from app.views.forms import SearchForm


class SearchFormTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()

    def tearDown(self):
        """
            Reset the test cases.
        """
        self.request_context.pop()
        self.app_context.pop()

    def test_search_param(self):
        """
            Test getting the search parameter.

            Expected result: The name of the search field including the form's prefix is returned.
        """
        prefix = 'text_'
        form = SearchForm(prefix=prefix)
        self.assertEqual(f'{prefix}search', form.search_param)

    def test_get_search_term_none(self):
        """
            Test getting the search term if there is none.

            Expected result: `None` is returned and set on the search field.
        """
        form = SearchForm()

        # Set some data on the search field to test that it is reset.
        form.search.data = 'Test Data'

        search_term = form.get_search_term()
        self.assertIsNone(search_term)
        self.assertIsNone(form.search.data)

    def test_get_search_term(self):
        """
            Test getting the search term if there is a search term.

            Expected result: The search term is returned and set on the search field.
        """
        search_term = 'Test Search'
        form = SearchForm()

        self.request_context.request.args = {form.search_param: search_term}

        search_term_from_request = form.get_search_term()
        self.assertEqual(search_term, search_term_from_request)
        self.assertEqual(search_term, form.search.data)
