#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    The entry point for the Aerarium application when run from the command line.
"""

from typing import Dict

from app import create_app
from app import db
from app import cli
from app.views.authorization import User

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context() -> Dict[str, object]:
    """
        Add default imports to the Flask shell.

        :return: A dictionary of objects that will be accessible in the Flask shell via their respective key.
    """
    context = {
        'db': db,
        'User': User,
    }

    return context
