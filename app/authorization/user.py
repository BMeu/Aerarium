#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Optional

from flask_babel import lazy_gettext as _l
from flask_login import login_user
from flask_login import logout_user
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Email

from app import bcrypt
from app import db
from app import login as app_login

"""
    The application's user model and related classes.
"""


class User(UserMixin, db.Model):
    """
        The class representing the application's users.
    """

    id = db.Column(db.Integer, primary_key=True)
    """
        The user's unique ID.
    """

    email = db.Column(db.String(255), index=True, unique=True)
    """
        The user's email address.
    """

    password_hash = db.Column(db.String(128))
    """
        The user's password, salted and hashed.
    """

    name = db.Column(db.String(255))
    """
        The user's (full) name.
    """

    _is_activated = db.Column('is_activated', db.Boolean, default=True)
    """
        Whether the user has activated their account.
    """

    def __init__(self, email: str, name: str) -> None:
        """
            Initialize the user.

            :param email: The user's email address.
            :param name: The user's (full) name.
        """
        self.email = email
        self.name = name

    @property
    def is_active(self) -> bool:
        """
            Determine if the user has activated their account.

            :return: ``True`` if the user account is activated.
        """
        return self._is_activated

    @is_active.setter
    def is_active(self, value: bool) -> None:
        """
            Set the activation status of this user account.

            :param value: ``True`` if the user account is activated.
        """
        self._is_activated = value

    def set_password(self, password: str) -> None:
        """
            Hash and set the given password.

            :param password: The plaintext password.
        """
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
            Check if the given password matches the user's password.

            :param password: The plaintext password to verify.
            :return: ``True`` if the ``password`` matches the user's password.
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        """
            Get a string representation of the user.

            :return: A string representation of the user.
        """
        return f'<User [{self.id}] {self.email}>'

    @staticmethod
    def login(email: str, password: str, remember_me: bool = False) -> Optional['User']:
        """
            Try to log in the user given by their email address and password.

            :param email: The user's email address.
            :param password: The user's (plaintext) password.
            :param remember_me: ``True`` if the user shall be kept logged in across sessions.
            :return: The user if the email/password combination is valid and the user is logged in, ``None`` otherwise.
        """

        user = User.query.filter_by(email=email).first()
        if user is None:
            return None

        if not user.check_password(password):
            return None

        logged_in = login_user(user, remember=remember_me)
        if not logged_in:
            return None

        return user

    @staticmethod
    def logout() -> bool:
        """
            Log out the user.

            :return: ``True`` on successful logout.
        """

        logged_out = logout_user()
        return logged_out

    @staticmethod
    @app_login.user_loader
    def load_from_db(user_id: int) -> Optional['User']:
        """
            Load the user with the given ID from the database.

            :param user_id: The ID of the user to load.
            :return: The loaded user if it exists, ``None`` otherwise.
        """

        return User.query.get(user_id)


class LoginForm(FlaskForm):
    """
        A form allowing a user to log in.
    """

    email = StringField(_l('Email:'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password:'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Log In'))
