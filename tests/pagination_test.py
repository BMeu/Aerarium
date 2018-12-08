#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from werkzeug.exceptions import NotFound

from app import create_app
from app import db
from app import Pagination
from app.configuration import TestConfiguration


class PaginationTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

        # Add a few test models.
        self.model_1 = TestModel()
        self.model_2 = TestModel()
        self.model_3 = TestModel()
        self.model_4 = TestModel()
        self.model_5 = TestModel()
        self.model_6 = TestModel()
        self.model_7 = TestModel()
        db.session.add(self.model_1)
        db.session.add(self.model_2)
        db.session.add(self.model_3)
        db.session.add(self.model_4)
        db.session.add(self.model_5)
        db.session.add(self.model_6)
        db.session.add(self.model_7)
        db.session.commit()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def test_init_success_default_page_param(self):
        """
            Test initializing the pagination object with the default page parameter.

            Expected result: All members are initialized.
        """
        current_page = 1
        self.request_context.request.args = {'page': current_page, 'p': current_page + 1}
        pagination = Pagination(TestModel.query)

        self.assertEqual(self.app.config['ITEMS_PER_PAGE'], pagination.rows_per_page)
        self.assertEqual(current_page, pagination.current_page)
        self.assertIsNotNone(pagination._rows)

    def test_init_success_custom_page_param(self):
        """
            Test initializing the pagination object with a custom page parameter.

            Expected result: All members are initialized.
        """
        current_page = 1
        self.request_context.request.args = {'page': current_page + 1, 'p': current_page}
        pagination = Pagination(TestModel.query, page_param='p')

        self.assertEqual(self.app.config['ITEMS_PER_PAGE'], pagination.rows_per_page)
        self.assertEqual(current_page, pagination.current_page)
        self.assertIsNotNone(pagination._rows)

    def test_init_wrong_current_page(self):
        """
            Test initializing the pagination object with a current page that does not exist.

            Expected result: An error is raised.
        """
        current_page = 4
        self.request_context.request.args = {'page': current_page}
        with self.assertRaises(NotFound):
            Pagination(TestModel.query)

    def test_first_row(self):
        """
            Test getting the first row index for all supported pages.

            Expected result: The corresponding first row is returned.
        """
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query)
        self.assertEqual(1, pagination.first_row)

        self.request_context.request.args = {'page': 2}
        pagination = Pagination(TestModel.query)
        self.assertEqual(4, pagination.first_row)

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)
        self.assertEqual(7, pagination.first_row)

    def test_last_row(self):
        """
            Test getting the last row index for all supported pages.

            Expected result: The corresponding last row is returned.
        """
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query,)
        self.assertEqual(3, pagination.last_row)

        self.request_context.request.args = {'page': 2}
        pagination = Pagination(TestModel.query)
        self.assertEqual(6, pagination.last_row)

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)
        self.assertEqual(7, pagination.last_row)

    def test_rows(self):
        """
            Test getting the actual rows for all supported pages.

            Expected results: The actual model objects for the requested page are returned.
        """
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query)
        self.assertListEqual([self.model_1, self.model_2, self.model_3], pagination.rows)

        self.request_context.request.args = {'page': 2}
        pagination = Pagination(TestModel.query)
        self.assertListEqual([self.model_4, self.model_5, self.model_6], pagination.rows)

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)
        self.assertListEqual([self.model_7], pagination.rows)

    def test_rows_on_page(self):
        """
            Test getting the number of rows on the current page for all supported pages.

            Expected result: The correct number is returned.
        """
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query)
        self.assertEqual(3, pagination.rows_on_page)

        self.request_context.request.args = {'page': 2}
        pagination = Pagination(TestModel.query)
        self.assertEqual(3, pagination.rows_on_page)

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)
        self.assertEqual(1, pagination.rows_on_page)

    def test_total_pages(self):
        """
            Test getting the number of total pages for all supported pages.

            Expected result: The return value is always the same.
        """
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query)
        self.assertEqual(3, pagination.total_pages)

        self.request_context.request.args = {'page': 2}
        pagination = Pagination(TestModel.query)
        self.assertEqual(3, pagination.total_pages)

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)
        self.assertEqual(3, pagination.total_pages)

    def test_total_rows(self):
        """
            Test getting the number of total rows for all supported pages.

            Expected result: The return value is always the same.
        """
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query)
        self.assertEqual(7, pagination.total_rows)

        self.request_context.request.args = {'page': 2}
        pagination = Pagination(TestModel.query)
        self.assertEqual(7, pagination.total_rows)

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)
        self.assertEqual(7, pagination.total_rows)

    def test_get_info_text_search_term_multiple(self):
        """
            Test getting the info text with a search term for multiple rows on a page.

            Expected result: The search term is included, the first and last row on the page are given.
        """

        self.request_context.request.args = {'page': 1}
        search_term = 'Aerarium'
        pagination = Pagination(TestModel.query)

        text = pagination.get_info_text(search_term)
        self.assertIn(f'results {pagination.first_row} to {pagination.last_row} of {pagination.total_rows}', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_search_term_single(self):
        """
            Test getting the info text with a search term for a single row on a page.

            Expected result: The search term is included, the first row on the page is given.
        """

        self.request_context.request.args = {'page': 3}
        search_term = 'Aerarium'
        pagination = Pagination(TestModel.query)

        text = pagination.get_info_text(search_term)
        self.assertIn(f'result {pagination.first_row} of {pagination.total_rows}', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_search_term_no_rows(self):
        """
            Test getting the info text with a search term for no rows on the page.

            Expected result: The search term is included, the info that no rows were found is given.
        """

        # Filter by some dummy value not related to the search term.
        self.request_context.request.args = {'page': 1}
        search_term = 'Aerarium'
        pagination = Pagination(TestModel.query.filter(TestModel.id > 42))

        text = pagination.get_info_text(search_term)
        self.assertIn('No results', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_no_search_term_multiple(self):
        """
            Test getting the info text without a search term for multiple rows on a page.

            Expected result: The search term is not included, the first and last row on the page are given.
        """

        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query)

        text = pagination.get_info_text()
        self.assertIn(f'results {pagination.first_row} to {pagination.last_row} of {pagination.total_rows}', text)
        self.assertNotIn(f'matching “', text)

    def test_get_info_text_no_search_term_single(self):
        """
            Test getting the info text without a search term for a single row on a page.

            Expected result: The search term is not included, the first row on the page is given.
        """

        self.request_context.request.args = {'page': 3}
        pagination = Pagination(TestModel.query)

        text = pagination.get_info_text()
        self.assertIn(f'result {pagination.first_row} of {pagination.total_rows}', text)
        self.assertNotIn(f'matching “', text)

    def test_get_info_text_no_search_term_no_rows(self):
        """
            Test getting the info text without a search term for no rows on the page.

            Expected result: The search term is not included, the info that no rows were found is given.
        """

        # Filter the results to achieve zero rows.
        self.request_context.request.args = {'page': 1}
        pagination = Pagination(TestModel.query.filter(TestModel.id > 42))

        text = pagination.get_info_text()
        self.assertIn('No results', text)
        self.assertNotIn(f'matching “', text)


class TestModel(db.Model):
    """
        A simple DB model used just for testing the pagination.
    """
    id = db.Column(db.Integer, primary_key=True)
