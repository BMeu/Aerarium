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

    def test_init(self):
        """
            Test initializing the form if a search term is set in the request.

            Expected result: The search term is set on the search field.
        """
        search_term = 'Test Search'
        self.request_context.request.args = {'search': search_term}

        form = SearchForm()
        self.assertEqual(search_term, form.search.data)

    def test_search_param(self):
        """
            Test getting the search parameter.

            Expected result: The name of the search field including the form's prefix is returned.
        """
        prefix = 'text_'
        form = SearchForm(prefix=prefix)
        self.assertEqual(f'{prefix}search', form.search_param)

    def test_search_term(self):
        """
            Test getting the search term from the form.

            Expected result: The data of the search field is returned.
        """
        search_term = 'Test SearchÄ'
        form = SearchForm()
        form.search.data = search_term

        self.assertEqual(search_term, form.search_term)

    def test_get_search_term_from_request_none(self):
        """
            Test getting the search term if there is none.

            Expected result: `None` is returned.
        """
        form = SearchForm()

        search_term = form._get_search_term_from_request()
        self.assertIsNone(search_term)

    def test_get_search_term_from_request(self):
        """
            Test getting the search term if there is a search term.

            Expected result: The search term is returned.
        """
        search_term = 'Test Search'
        form = SearchForm()

        self.request_context.request.args = {form.search_param: search_term}

        search_term_from_request = form._get_search_term_from_request()
        self.assertEqual(search_term, search_term_from_request)
