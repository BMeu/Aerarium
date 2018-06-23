#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Extensions to the command-line interface provided by Flask.
"""

import os

import click
from flask import Flask


def register(application: Flask) -> None:
    """
        Register command-line interface options.

        :param application: The Flask application instance for which the CLI will be registered.
    """

    # Babel configuration.
    babel_cmd = 'pybabel'
    babel_config = 'babel.cfg'
    babel_keywords = [
        '_l',
    ]
    babel_pot_file = os.path.join(application.config['TMP_DIR'], 'messages.pot')
    babel_translation_dir = os.path.join(application.config['BASE_DIR'], 'app', 'translations')

    @application.cli.group()
    def translate() -> None:
        """
            Translation and localization commands.
        """
        pass

    # noinspection PyShadowingBuiltins
    @translate.command(name='compile', help='Compile all languages.')
    def translate_compile() -> None:
        """
            Compile all languages.

            :raise RuntimeError: In case of pybabel command failures.
        """

        if os.system(f'{babel_cmd} compile -d {babel_translation_dir}'):
            raise RuntimeError('PyBabel: Compilation failed.')

    @translate.command(name='init', help='Initialize a new language with the given LANGUAGE code.')
    @click.argument('language')
    def translate_init(language: str) -> None:
        """
            Initialize a new language.

            :param language: The code of the language to initialize.
            :raise RuntimeError: In case of pybabel command failures.
        """

        _translate_extract()

        if os.system(f'{babel_cmd} init -i {babel_pot_file} -d {babel_translation_dir} -l {language}'):
            raise RuntimeError('PyBabel: Language initialization failed.')

        os.remove(babel_pot_file)

    @translate.command(name='update', help='Update all languages.')
    def translate_update() -> None:
        """
            Update all languages.

            :raise RuntimeError: In case of pybabel command failures.
        """

        _translate_extract()

        if os.system(f'{babel_cmd} update -i {babel_pot_file} -d {babel_translation_dir}'):
            raise RuntimeError('PyBabel: Update failed.')

        os.remove(babel_pot_file)

    def _translate_extract() -> None:
        """
            Extract all translatable strings.

            :raise RuntimeError: In case of pybabel command failures.
        """

        keywords = ' '.join(babel_keywords)
        if os.system(f'{babel_cmd} extract -F {babel_config} -k {keywords} -o {babel_pot_file} .'):
            raise RuntimeError('PyBabel: Extraction failed.')
