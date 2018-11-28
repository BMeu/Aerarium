#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Localization helpers.
"""

from app.localization.languages import get_default_language
from app.localization.languages import get_language_names
from app.localization.languages import get_languages
from app.localization.languages import get_locale

__all__ = [
            'get_default_language',
            'get_language_names',
            'get_languages',
            'get_locale',
          ]
