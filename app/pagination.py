#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Pagination functionality.
"""

from typing import List
from typing import Optional

from flask_babel import gettext as _
from flask_sqlalchemy import BaseQuery

from app import db
from app import get_app


class Pagination(object):
    """
        A helper object providing basic functionality for all paginations.
    """

    def __init__(self, query: BaseQuery, current_page: int) -> None:
        """
            Initialize the pagination object.

            If the current page does not exists the request will be aborted with an status code 404.

            :param query: The base query that will be paginated.
            :param current_page: The page that is currently displayed.
        """
        application = get_app()
        self.rows_per_page = application.config['ITEMS_PER_PAGE']
        self.current_page = current_page

        self._rows = query.paginate(self.current_page, self.rows_per_page)

    @property
    def first_row(self) -> int:
        """
            The index of the first row.

            :return: The number of the first row on the current page.
        """
        rows_on_previous_page = (self.current_page - 1) * self.rows_per_page
        return rows_on_previous_page + 1

    @property
    def last_row(self) -> int:
        """
            The index of the last row.

            :return: The number of the last row on the current page.
        """
        return self.first_row + self.rows_on_page - 1

    @property
    def rows(self) -> List[db.Model]:
        """
            Get the actual objects for the current page.

            :return: The SQLAlchemy models shown on the current page.
        """
        return self._rows.items

    @property
    def rows_on_page(self) -> int:
        """
            Get the number of rows that are displayed on the current page.

            :return: The number of rows in the page.
        """
        return len(self.rows)

    @property
    def total_pages(self) -> int:
        """
            Get the number of total pages.

            :return: The number of pages needed to display all rows.
        """
        return self._rows.pages

    @property
    def total_rows(self) -> int:
        """
            The number of total rows.

            :return: The number of total rows across all pages.
        """
        return self._rows.total

    def get_info_text(self, search_term: Optional[str] = None) -> str:
        """
            Get an informational text explaining how many results are being displayed on the current page.

            :param search_term: If given, this term will be included in the info text to explain that the results are
                                being filtered by this value.
            :return: The info text.
        """

        # Text with a search.
        if search_term:

            # More than one result on the page.
            if self.rows_on_page >= 2:
                return _('Displaying results %(first_result)d to %(last_result)d of %(total_results)d matching '
                         '“%(search)s”',
                         first_result=self.first_row, last_result=self.last_row, total_results=self.total_rows,
                         search=search_term)

            # One result on the page.
            if self.rows_on_page == 1:
                return _('Displaying result %(result)d of %(total_results)d matching “%(search)s”',
                         result=self.first_row, total_results=self.total_rows, search=search_term)

            # No results.
            return _('No results found matching “%(search)s”', search=search_term)

        # Text without a search.

        # More than one result on the page.
        if self.rows_on_page >= 2:
            return _('Displaying results %(first_result)d to %(last_result)d of %(total_results)d',
                     first_result=self.first_row, last_result=self.last_row, total_results=self.total_rows)

        # One result on the page.
        if self.rows_on_page == 1:
            return _('Displaying result %(result)d of %(total_results)d',
                     result=self.first_row, total_results=self.total_rows)

        # No results.
        return _('No results')
