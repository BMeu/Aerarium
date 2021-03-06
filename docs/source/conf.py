# -*- coding: utf-8 -*-

"""
    Configuration file for the Sphinx documentation builder.
"""

import os
import sys

# Find the source code.
sys.path.insert(0, os.path.abspath('../..'))


"""
    PROJECT INFORMATION
"""

# General Information

# TODO: Update version before releases.
AUTHOR = 'Bastian Meyer'
DESCRIPTION = 'Managing Your Finances'
PROJECT = 'Aerarium'
VERSION = '0.1.0'

author = AUTHOR
# noinspection PyShadowingBuiltins
copyright = f'Developed by {AUTHOR}. {PROJECT} is licensed under the MIT license.'
project = PROJECT
release = VERSION
version = VERSION

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

add_module_names = False
autoclass_content = 'both'
language = None
master_doc = 'index'
pygments_style = 'sphinx'
source_suffix = '.rst'
templates_path = ['_templates']

rst_prolog = ('.. |project| replace:: {name}\n'
              '.. include:: <isonum.txt>').format(name=PROJECT)


"""
    HTML OUTPUT
"""

html_domain_indices = True
html_static_path = ['_static']
html_use_index = False

# Theme options.
html_theme = 'alabaster'
html_theme_options = {
    'description': f'{PROJECT}: {DESCRIPTION}',
    'logo': 'logo.png',
    'github_banner': True,
    'github_user': 'BMeu',
    'github_repo': 'Aerarium',
    'travis_button': True,
    'codecov_button': True,
    'page_width': '1200px',
    'sidebar_width': '300px'
}

html_sidebars = {
    '**': ['about.html', 'navigation.html', 'searchbox.html']
}


"""
    HTML HELP OUTPUT
"""

htmlhelp_basename = f'{PROJECT}doc'


"""
    LATEX OUTPUT
"""

latex_documents = [
    (master_doc, f'{PROJECT}.tex', f'{PROJECT} Documentation', author, 'manual'),
]

latex_elements = {
    'papersize': 'a4paper',
}


"""
    MANPAGE OUTPUT
"""

man_pages = [
    (master_doc, 'aerarium', f'{PROJECT} Documentation', [author], 1)
]


"""
    TEXINFO OUTPUT
"""

texinfo_documents = [
    (master_doc, PROJECT, f'{PROJECT} Documentation', author, PROJECT, DESCRIPTION, 'Miscellaneous'),
]


"""
    EXTENSION CONFIGURATION
"""

todo_include_todos = True
