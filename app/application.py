#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Application initialization.
"""

from typing import Optional

from logging import ERROR
from logging import Formatter as LoggingFormatter
from logging import INFO
import os
import sys
from typing import Type

from flask import current_app
from flask import Flask
from flask.logging import default_handler
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from app import register_after_request_handlers
from app import register_before_request_handlers
from app.configuration import BaseConfiguration
from app.localization import get_locale
from app.logging import create_file_handler
from app.logging import create_mail_handler
from app.logging import create_stream_handler

# Create the extension objects.
babel = Babel()
bcrypt = Bcrypt()
csrf = CSRFProtect()
db = SQLAlchemy()
login = LoginManager()
mail = Mail()
migrate = Migrate()


def create_app(configuration_class: Type[BaseConfiguration] = BaseConfiguration) -> Flask:
    """
        Create and initialize a new app instance.

        :param configuration_class: The class from which the configuration will be loaded.
        :return: An initialized Flask application.
    """

    application = Flask(__name__, instance_path=configuration_class.INSTANCE_DIR)
    application.config.from_object(configuration_class)

    _initialize_extensions(application)
    _initialize_blueprints(application)

    register_before_request_handlers(application)
    register_after_request_handlers(application)

    # If the application is running in production mode, enable logging and ensure some configuration variables.
    if not application.debug and not application.testing:  # pragma: no cover
        _initialize_logging(application)
        application.logger.info('{app_name} Startup'.format(app_name=application.config['TITLE_SHORT']))

        # Warn on missing system administrator addresses (no logs can be sent) if a mail server is configured.
        if application.config['MAIL_SERVER'] and application.config['SYS_ADMINS'] is None:
            message = 'No system administrator email addresses defined. In case of severe failures, logs cannot be '\
                    'sent by mail.'
            application.logger.warn(message)

        # Exit on missing a secret key (user sessions cannot be encrypted).
        if application.config['SECRET_KEY'] is None:
            message = 'No secret key defined. Set one using the configuration variable SECRET_KEY. Exiting due to '\
                    'severe security vulnerabilities without a secret key in production mode.'
            print(message)
            application.logger.error(message)
            sys.exit(1)

    return application


def get_app() -> Optional[Flask]:
    """
        Get the application instance object.

        :return: The application object. ``None`` if it does not exist (e.g. when working outside the app context).
    """
    try:
        # noinspection PyProtectedMember
        application = current_app._get_current_object()
    except (AttributeError, RuntimeError):
        application = None

    return application


def _initialize_blueprints(application: Flask) -> None:
    """
        Initialize the blueprints.

        :param application: The application instance for which the blueprints will be registered.
    """
    from app.views.administration import bp as administration_bp
    from app.views.main import bp as main_bp
    from app.views.userprofile import bp as userprofile_bp

    application.register_blueprint(administration_bp, url_prefix='/administration')
    application.register_blueprint(main_bp)
    application.register_blueprint(userprofile_bp, url_prefix='/user')


def _initialize_extensions(application: Flask) -> None:
    """
        Initialize the Flask extensions.

        :param application: The application instance for which the extensions will be registered.
    """
    babel.init_app(application)
    babel.locale_selector_func = get_locale

    bcrypt.init_app(application)

    csrf.init_app(application)

    db.init_app(application)

    login.init_app(application)
    login.login_message = _l('Please log in to access this page.')
    login.login_message_category = 'error'
    login.login_view = 'userprofile.login'

    mail.init_app(application)

    migrate.init_app(application, db)


def _initialize_logging(application: Flask) -> None:  # pragma: no cover
    """
        Initialize error logging.

        :param application: The application instance for which logging will be initialized.
    """

    # Remove the default handler to avoid unexpected log entries in STDOUT.
    application.logger.removeHandler(default_handler)

    line_format = LoggingFormatter('%(asctime)s [%(levelname)s] in %(module)s [%(pathname)s:%(lineno)d]: %(message)s')

    # Send errors via mail to sys admins.
    if application.config['MAIL_SERVER'] and application.config['SYS_ADMINS']:
        sender = application.config['MAIL_FROM']
        recipients = application.config['SYS_ADMINS']
        subject = '{app_name} Failure'.format(app_name=application.config['TITLE_SHORT'])
        server = application.config['MAIL_SERVER']
        port = application.config['MAIL_PORT']
        username = application.config['MAIL_USERNAME']
        password = application.config['MAIL_PASSWORD']
        tls = application.config['MAIL_USE_TLS']
        ssl = application.config['MAIL_USE_SSL']

        mail_handler = create_mail_handler(ERROR, line_format, sender, recipients, subject, server, port, username,
                                           password, tls, ssl)
        application.logger.addHandler(mail_handler)

    # Log information and higher events.
    if application.config['LOG_TO_STDOUT']:
        stream_handler = create_stream_handler(INFO, line_format)
        application.logger.addHandler(stream_handler)
    else:
        log_dir = application.config['LOG_DIR']
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        log_file = os.path.join(log_dir, 'app.log')
        max_kb = application.config['LOG_FILE_MAX_KB']
        max_files = application.config['LOG_MAX_FILES']

        file_handler = create_file_handler(INFO, line_format, log_file, max_kb, max_files)
        application.logger.addHandler(file_handler)

    application.logger.setLevel(INFO)
