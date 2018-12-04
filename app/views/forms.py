#!venv/bin/python
# -*- coding: utf-8 -*-

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
    """
    search = StringField(_l('Search:'))
    submit = SubmitField(_l('Search'))

# endregion
