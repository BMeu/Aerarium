# -*- coding: utf-8 -*-

"""
    Extensions to the command-line interface provided by Flask.
"""

from typing import Optional

import os
import sys
from time import time

import click
from flask import Flask
from flask_bcrypt import generate_password_hash


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

    @application.cli.command(name='pw_hash_rounds',  # type: ignore
                             help='Determine the number of bcrypt hashing rounds that can be handled within the '
                                  'given maximum time MAX_TIME (in ms).')
    @click.argument('max_time')
    @click.option('-v', '--verbose', default=False, is_flag=True,
                  help='Show the duration for all tried number of rounds.')
    def pw_hash_rounds(max_time: str, verbose: Optional[bool] = False) -> None:
        """
            Determine the number of bcrypt log rounds that can be handled within the given maximum time `max_time`.

            :param verbose: Show the duration for all tried number of rounds.
            :param max_time: The maximum time allowed for password hashing in milliseconds.
        """

        max_duration = float(max_time)
        password = 'Aerarium'

        # Bcrypt allows only 4 to 31 rounds of hashing.
        min_rounds = 4
        max_rounds = 31

        rounds = min_rounds
        for rounds in range(min_rounds, max_rounds + 1):
            start = time()

            generate_password_hash(password, rounds)

            stop = time()
            duration = (stop - start) * 1000.0

            if verbose:
                click.echo(f'Rounds: {rounds:02d} | Duration: {duration:.1f}ms')

            if duration > max_duration:
                # If the duration is larger than the maximum time, the last number of rounds gives the correct result.
                rounds -= 1
                break
        else:
            if verbose:
                click.echo('Reached maximum number of hashing rounds.')

        if verbose:
            # Insert a line break to separate the verbose output from the relevant information.
            click.echo('')

        if rounds < min_rounds:
            # If the found number of rounds is smaller than the minimum number of rounds, the minimum number has taken
            # more time than requested. However, this value is not allowed by bcrypt.
            rounds = min_rounds
            click.echo(f'The minimum number of rounds took more time than allowed.')
            click.echo(f'However, the number of rounds must be at least: {rounds}')
        else:
            click.echo(f'Found suiting number of hashing rounds: {rounds}')

        click.echo(f'You can set this value in your configuration file with')
        click.echo(f'   BCRYPT_LOG_ROUNDS={rounds}')

    @application.cli.group()  # type: ignore
    def translate() -> None:
        """
            Translation and localization commands.
        """

        pass

    # noinspection PyShadowingBuiltins
    @translate.command(name='compile', help='Compile all languages.')  # type: ignore
    def translate_compile() -> None:
        """
            Compile all languages.

            :raise RuntimeError: In case of pybabel command failures.
        """

        if os.system(f'{babel_cmd} compile -d {babel_translation_dir}'):
            click.echo('PyBabel: Compilation failed.')
            sys.exit(1)

    @translate.command(name='init', help='Initialize a new language with the given LANGUAGE code.')  # type: ignore
    @click.argument('language')
    def translate_init(language: str) -> None:
        """
            Initialize a new language.

            :param language: The code of the language to initialize.
            :raise RuntimeError: In case of pybabel command failures.
        """

        _translate_extract()

        if os.system(f'{babel_cmd} init -i {babel_pot_file} -d {babel_translation_dir} -l {language}'):
            click.echo('PyBabel: Language initialization failed.')
            sys.exit(1)

        os.remove(babel_pot_file)

    @translate.command(name='update', help='Update all languages.')  # type: ignore
    def translate_update() -> None:
        """
            Update all languages.

            :raise RuntimeError: In case of pybabel command failures.
        """

        _translate_extract()

        if os.system(f'{babel_cmd} update -i {babel_pot_file} -d {babel_translation_dir}'):
            click.echo('PyBabel: Update failed.')
            sys.exit(1)

        os.remove(babel_pot_file)

    def _translate_extract() -> None:
        """
            Extract all translatable strings.

            :raise RuntimeError: In case of pybabel command failures.
        """

        keywords = ' '.join(babel_keywords)
        if os.system(f'{babel_cmd} extract -F {babel_config} -k {keywords} -o {babel_pot_file} .'):
            click.echo('PyBabel: Extraction failed.')
            sys.exit(1)
