#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Optional

from flask import request
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField

"""
    Forms and form related functionality for the all blueprints.
"""

# region Forms


class SearchForm(FlaskForm):
    """
        A form for searching.

        This form is intended to be used for GET requests without further validation.
    """
    search = StringField(_l('Search:'))
    submit = SubmitField(_l('Search'))

    @property
    def search_param(self) -> str:
        """
            Get the search parameter for the URL.

            :return: The name of the
        """
        return self.search.name

    def get_search_term(self) -> Optional[str]:
        """
            Get the search term from the URL.

            This will also set the term on the search field.

            :return: The string for which the user searched. `None` if the user did not search for anything.
        """
        term = request.args.get(self.search_param, None)
        self.search.data = term
        return term

# endregion
