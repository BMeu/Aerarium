#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Configurations for the application.
"""

from app.configuration.base_configuration import BaseConfiguration
from app.configuration.test_configuration import TestConfiguration

__all__ = [
            'BaseConfiguration',
            'TestConfiguration'
          ]
