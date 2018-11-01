# Aerarium


[![Build Status](https://travis-ci.org/BMeu/Aerarium.svg?branch=master)](https://travis-ci.org/BMeu/Aerarium)
[![codecov](https://codecov.io/gh/BMeu/Aerarium/branch/master/graph/badge.svg)](https://codecov.io/gh/BMeu/Aerarium)

**Aerarium:** Managing Your Finances

## Getting Started

### System Requirements

* Python 3.6

### Installation

### Configuration

Aerarium allows configuration in two ways: you can either use environment variables or use a `.env` file in the
[`instance`](instance) folder. All configuration options are explained in the included example file
[`instance/example.env`](instance/example.env). To use your own settings, simply rename this file to `.env`. All of the
options can also directly be used as environment variables instead. 

## Contribution

Your contribution is greatly appreciated!

### Ideas, Requests and Bug Reports

If you have ideas for new features or want to report a bug you can
[create a new issue on GitHub](https://github.com/BMeu/Aerarium/issues/new). 
  
### Languages

Do you want to see Aerarium in your language, but you don't know how to or don't want to
[set up an entire development environment](#development)? In this case, you can
[create a new issue on GitHub](https://github.com/BMeu/Aerarium/issues/new). Please include the language you want to
translate into, the country if you want to translate into a country-specific dialect (e.g. Brazilian Portuguese), and
the name under which you want to appear in the [list of translators](#translations). Also, shortly explain why you are
suited to translate into that language. I will then send you a translation file in the
[Gettext](https://en.wikipedia.org/wiki/Gettext) format. You can edit this file either in a text editor or a special
editor (for example, the free [Poedit](https://poedit.net/) that is available for all major systems). Once you are done
with your translation, send the file back to me. I will then add it to the project. 

### Development 

If you do not want to wait for me to implement your requests you can implement those changes yourself and submit a pull
request.

#### Setting Up the Development Environment

Ensure your system fulfills the [requirements](#system-requirements). Additionally, you will also need ``virtualenv``
for Python 3.6. Then execute the following commands in your terminal (on Unix systems; assuming your executable for
Python in the required version is called ``python3``) to set up your development environment:

```bash
git clone https://github.com/BMeu/Aerarium.git
cd Aerarium
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
export FLASK_APP=aerarium.py
flask translate compile
```

Remember to [set up your configuration](#configuration) as well!

#### Running Locally

You can run a local test server on your PC to directly test your changes:

```bash
export DEBUG=1
flask run
```

All ``flask`` commands require that the environment variable ``FLASK_APP`` is set to ``aerarium.py``.

#### Translating

If you want to add a new language run:

```bash
flask translate init LANGUAGE
```

In order to update translations with newly added texts run:

```bash
flask translate update
```

If you changed a translation you can compile the changes with the following command:

```bash
flask translate compile
```

If you add a new language do not forget to add yourself to the [list of translators](#translations) below.

#### Submitting a Pull Request

When you submit a pull request, please ensure that your changes fulfill the following points:

* No linter errors:
    ```bash
    flake8
    ```
* Functions, methods and class members specify full type hints (except for ``cls`` and ``self``).
* All packages, modules, classes, methods, functions, members, etc. are fully documented.
* The documentation builds without errors:
    ```bash
    sphinx-apidoc -o docs/source/api app app/configuration
    sphinx-build -b html docs/source docs/build
    ```
* All tests pass:
    ```bash
    python -m unittest discover -v -s tests -p "*_test.py" -t .
    ```
* All functions and methods have a unit test, no matter how trivial the code may seem (one unit test per scenario).
* The tests reach a code coverage of 100% (exceptions may be discussed individually):
    ```bash
    coverage run -m unittest discover -v -s tests -p "*_test.py" -t .
    coverage report
    ```
* Imports are structured in four blocks in the following order, with a blank line separating each block:
    1. Type imports, e.g. ``from typing import Optional``
    2. System libraries, e.g. ``from threading import Thread``
    3. Third-party libraries, e.g. ``from flask import render_template``
    4. Project modules, e.g. ``from app.authorization import User``
* Each import is on its own line, ordered alphabetically, e.g.
    
    ```python
    from flask import render_template
    from flask import url_for
    from flask_login import login_user
    ```
    
    but **not**
    
    ```python
    from flask_login import login_user
    from flask import url_for, render_template
    ```
    
    This makes it easier to find imports and spot changes in commits.
* If you need to add a new package dependency only add the package itself to the ``requirements.txt`` file (i.e. do not
  include the package's dependencies as well). That is, do **not** run ``pip freeze > requirements.txt``! This ensures
  that there are no unused indirect dependencies because a direct dependency changed.
* All texts that are displayed to the user must be localizable. If you added, changed, or deleted some of those texts
  put a note in the pull request so the translators can be informed, and update the translation files:
  ```bash
  flask translate update
  ``` 

## Translations

| Language | Translator | Status |
|----------|------------|--------|
| English  | [Bastian Meyer](https://www.bastianmeyer.eu) | 100% |
| German   | [Bastian Meyer](https://www.bastianmeyer.eu) | 100% |


## License

Aerarium is developed by [Bastian Meyer](https://www.bastianmeyer.eu)
<[bastian@bastianmeyer.eu](mailto:bastian@bastianmeyer.eu)> and is licensed under the
[MIT License]((http://www.opensource.org/licenses/MIT)). For details, see the attached [LICENSE](LICENSE) file. 
