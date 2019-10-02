#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Any
from typing import Optional

from flask import request
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField

"""
    Forms and form related functionality for all blueprints.
"""

# region Forms


class SearchForm(FlaskForm):
    """
        A form for searching.

        This form is intended to be used for GET requests without further validation.
    """
    search = StringField(_l('Search:'))
    """
        The search field.
    """

    submit = SubmitField(_l('Search'))
    """
        The submit button.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """
            The search field will automatically be filled from the request.

            :param args: The arguments for initializing the form.
            :param kwargs: The keyworded arguments for initializing the form.
        """
        super().__init__(*args, **kwargs)

        search_term = self._get_search_term_from_request()
        self.search.data = search_term

    @property
    def search_param(self) -> str:
        """
            Get the search parameter for the URL.

            :return: The name of the URL parameter that contains the search term.
        """
        return self.search.name  # type: ignore

    @property
    def search_term(self) -> Optional[str]:
        """
            Get the term for which the user searched.

            :return: The string for which the user searched. ``None`` if the user did not search for anything.
        """
        return self.search.data  # type: ignore

    def _get_search_term_from_request(self) -> Optional[str]:
        """
            Get the search term from the URL.

            :return: The string for which the user searched. ``None`` if the user did not search for anything.
        """
        term = request.args.get(self.search_param, None)
        return term

# endregion
