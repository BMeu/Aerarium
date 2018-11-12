#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Any
from typing import Callable
from typing import Optional
from typing import Tuple

from functools import wraps

from flask import redirect
from flask import render_template
from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import Field
from wtforms import Form
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo

from app import bcrypt
from app import db
from app import get_app
from app import login as app_login
from app import send_email
from app.authorization.tokens import ChangeEmailAddressToken
from app.authorization.tokens import DeleteAccountToken
from app.authorization.tokens import ResetPasswordToken

"""
    The application's user model and related classes.
"""


class User(UserMixin, db.Model):
    """
        The class representing the application's users.
    """

    # region Fields and Properties

    id = db.Column(db.Integer, primary_key=True)
    """
        The user's unique ID.
    """

    _email = db.Column('email', db.String(255), index=True, unique=True)
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

    # endregion

    # region Initialization

    def __init__(self, email: str, name: str) -> None:
        """
            Initialize the user.

            :param email: The user's email address.
            :param name: The user's (full) name.
        """
        self.set_email(email)
        self.name = name

    @staticmethod
    @app_login.user_loader
    def load_from_id(user_id: int) -> Optional['User']:
        """
            Load the user with the given ID from the database.

            :param user_id: The ID of the user to load.
            :return: The loaded user if it exists, ``None`` otherwise.
        """

        return User.query.get(user_id)

    @staticmethod
    def load_from_email(email: str) -> Optional['User']:
        """
            Load the user with the given email address from the database.

            :param email: The email address of the user to load.
            :return: The loaded user if it exists, ``None`` otherwise.
        """

        return User.query.filter_by(_email=email).first()

    # endregion

    # region Email

    def get_email(self) -> str:
        """
            Get the user's email address.

            :return: The user's email address.
        """
        return self._email

    def set_email(self, email: str) -> bool:
        """
            Change the user's email address to the new given one.

            :param email: The user's new email address. Must not be used by a different user.
            :return: ``False`` if the email address already is in use by another user, ``True`` otherwise.
        """

        old_email = self.get_email()
        if old_email == email:
            return True

        user = User.load_from_email(email)
        if user is not None and user != self:
            return False

        self._email = email
        if not old_email:
            # If there is no old email the user has just been created. Do not send an email in this case.
            return True

        application = get_app()
        support_address = application.config.get('SUPPORT_ADDRESS', None)
        body_plain = render_template('authorization/emails/email_changed_plain.txt',
                                     name=self.name, new_email=email, support_email=support_address)
        body_html = render_template('authorization/emails/email_changed_html.html',
                                    name=self.name, new_email=email, support_email=support_address)

        send_email(_('Your Email Address Has Been Changed'), [old_email], body_plain, body_html)

        return True

    def send_change_email_address_email(self, email: str) -> ChangeEmailAddressToken:
        """
            Send a token to the user to change their email address.

            :param email: The email address to which the token will be sent and to which the user's email will be
                          changed upon verification.
            :return: The token send in the mail.
        """

        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = self.id
        token_obj.new_email = email

        token = token_obj.create()
        validity = token_obj.get_validity(in_minutes=True)

        link = url_for('authorization.change_email', token=token, _external=True)

        email_old = self.get_email()
        body_plain = render_template('authorization/emails/change_email_address_plain.txt',
                                     name=self.name, link=link, validity=validity, email_old=email_old, email_new=email)
        body_html = render_template('authorization/emails/change_email_address_html.html',
                                    name=self.name, link=link, validity=validity, email_old=email_old, email_new=email)

        send_email(_('Change Your Email Address'), [email], body_plain, body_html)
        return token_obj

    @staticmethod
    def verify_change_email_address_token(token: str) -> Tuple[Optional['User'], Optional[str]]:
        """
            Verify the JWT to change a user's email address.

            :param token: The change-email token.
            :return: The user to which the token belongs and the new email address; both are ``None`` if the token is
                     invalid.
        """
        token_obj = ChangeEmailAddressToken.verify(token)
        user = User.load_from_id(token_obj.user_id)
        return user, token_obj.new_email

    # endregion

    # region Password

    def set_password(self, password: str) -> None:
        """
            Hash and set the given password.

            :param password: The plaintext password.
        """

        if not password:
            return

        # If the password stayed the same do not do anything; especially, do not send an email.
        if self.check_password(password):
            return

        # If the user does not have a password at the moment, their account has been newly created. Do not send an email
        # in this case.
        if self.password_hash is not None:
            application = get_app()

            support_address = application.config.get('SUPPORT_ADDRESS', None)
            body_plain = render_template('authorization/emails/password_changed_plain.txt',
                                         name=self.name, support_email=support_address)
            body_html = render_template('authorization/emails/password_changed_html.html',
                                        name=self.name, support_email=support_address)

            send_email(_('Your Password Has Been Changed'), [self.get_email()], body_plain, body_html)

        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
            Check if the given password matches the user's password.

            :param password: The plaintext password to verify.
            :return: ``True`` if the ``password`` matches the user's password.
        """
        if not self.password_hash:
            return False

        return bcrypt.check_password_hash(self.password_hash, password)

    def send_password_reset_email(self) -> Optional[ResetPasswordToken]:
        """
            Send a mail for resetting the user's password to their email address.

            :return: The token send in the mail
        """

        if self.get_email() is None:
            return None

        token_obj = ResetPasswordToken()
        token_obj.user_id = self.id
        token = token_obj.create()

        validity = token_obj.get_validity(in_minutes=True)

        link = url_for('authorization.reset_password', token=token, _external=True)

        body_plain = render_template('authorization/emails/reset_password_plain.txt',
                                     name=self.name, link=link, validity=validity)
        body_html = render_template('authorization/emails/reset_password_html.html',
                                    name=self.name, link=link, validity=validity)

        send_email(_('Reset Your Password'), [self.get_email()], body_plain, body_html)
        return token_obj

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional['User']:
        """
            Verify a given token for resetting a password.

            :param token: The password-reset JWT.
            :return: The user for whom the token is valid. ``None`` if the token is invalid or if outside the
                     application context.
        """
        token_obj = ResetPasswordToken.verify(token)
        return User.load_from_id(token_obj.user_id)

    # endregion

    # region Login/Logout

    @staticmethod
    def login(email: str, password: str, remember_me: bool = False) -> Optional['User']:
        """
            Try to log in the user given by their email address and password.

            :param email: The user's email address.
            :param password: The user's (plaintext) password.
            :param remember_me: ``True`` if the user shall be kept logged in across sessions.
            :return: The user if the email/password combination is valid and the user is logged in, ``None`` otherwise.
        """

        user = User.load_from_email(email)
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

    # endregion

    # region Delete

    def send_delete_account_email(self) -> DeleteAccountToken:
        """
            Send a token to the user to confirm their intention to delete their account.

            :return: The token sent in the mail.
        """
        token_obj = DeleteAccountToken()
        token_obj.user_id = self.id

        token = token_obj.create()
        validity = token_obj.get_validity(in_minutes=True)

        link = url_for('authorization.delete_account', token=token, _external=True)

        body_plain = render_template('authorization/emails/delete_account_request.txt',
                                     name=self.name, link=link, validity=validity)

        body_html = render_template('authorization/emails/delete_account_request.html',
                                    name=self.name, link=link, validity=validity)
        send_email(_('Delete Your User Profile'), [self.get_email()], body_plain, body_html)

        return token_obj

    @staticmethod
    def verify_delete_account_token(token: str) -> Optional['User']:
        """
            Verify the JWT to delete a user's account.

            :param token: The delete-account token.
            :return: The user to which the token belongs; ``None`` if the token is invalid.
        """
        token_obj = DeleteAccountToken.verify(token)
        user = User.load_from_id(token_obj.user_id)
        return user

    def delete(self) -> None:
        """
            Delete the user's account. Log them out first if necessary. Notify them via mail.
        """
        if self == current_user:
            self.logout()

        # Notify the user via email.
        application = get_app()
        support_address = application.config.get('SUPPORT_ADDRESS', None)
        body_plain = render_template('authorization/emails/delete_account_confirmation.txt',
                                     name=self.name, new_email=self.get_email(), support_email=support_address)
        body_html = render_template('authorization/emails/delete_account_confirmation.html',
                                    name=self.name, new_email=self.get_email(), support_email=support_address)
        send_email(_('Your User Profile Has Been Deleted'), [self.get_email()], body_plain, body_html)

        db.session.delete(self)
        db.session.commit()

    # endregion

    # region System

    def __repr__(self) -> str:
        """
            Get a string representation of the user.

            :return: A string representation of the user.
        """
        return f'<User [{self.id}] {self.get_email()}>'

    # endregion

# region Decorators


def logout_required(view_function: Callable[..., str]) -> Callable[..., str]:
    """
        A wrapper for view functions requiring the current user to be logged out. If the current user is logged in
        they will be redirected to the home page.

        :param view_function: The Flask view function being wrapped.
        :return: The wrapped view function.
    """

    @wraps(view_function)
    def wrapped_logout_required(*args: Any, **kwargs: Any) -> str:
        """
            If the current user is logged in, redirect to the home page. Otherwise, execute the wrapped view function.

            :param args: The arguments of the view function.
            :param kwargs: The keyword arguments of the view function.
            :return: The response of either the home page view function or the wrapped view function.
        """
        if current_user is not None and current_user.is_authenticated:
            return redirect(url_for('main.index'))

        return view_function(*args, **kwargs)

    return wrapped_logout_required

# endregion

# region Forms


class UniqueEmail(object):
    """
        A WTForms validator to verify that an entered email address is not yet in use by a user other than the current
        one.
    """

    def __init__(self, message=None) -> None:
        """
            Initialize the validator.

            :param message: The error message shown to the user if the validation fails.
        """

        if not message:
            message = _l('The email address already is in use.')

        self.message = message

    def __call__(self, form: Form, field: Field) -> None:
        """
            Execute the validator.

            :param form: The form to which the field belongs.
            :param field: The field to which this validator is attached.
            :raise ValidationError: In case the validation fails.
        """
        email = field.data
        if not email:
            return

        # If there already is a user with that email address and this user is not the current user, this is an error.
        user = User.load_from_email(email)
        if user and user != current_user:
            raise ValidationError(self.message)


class AccountForm(FlaskForm):
    """
        A form allowing a user to change their account details.
    """
    name = StringField(_l('Name:'), validators=[DataRequired()])
    email = StringField(_l('Email:'), validators=[DataRequired(), Email(), UniqueEmail()],
                        description=_l('We will send you an email to your new address with a link to confirm the \
                                        changes. The email address will not be changed until you confirm this action.'))
    password = PasswordField(_l('New Password:'),
                             description=_l('Leave this field empty if you do not want to change your password.'))
    password_confirmation = PasswordField(_l('Confirm Your New Password:'), validators=[EqualTo('password')])
    submit = SubmitField(_l('Save'))


class EmailForm(FlaskForm):
    """
        A form requesting a user to enter their email address.
    """

    email = StringField(_l('Email:'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Submit'))


class LoginForm(FlaskForm):
    """
        A form allowing a user to log in.
    """

    email = StringField(_l('Email:'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password:'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Log In'))


class PasswordResetForm(FlaskForm):
    """
        A form for resetting a user's password.
    """

    password = PasswordField(_l('New Password:'), validators=[DataRequired()])
    password_confirmation = PasswordField(_l('Confirm Your New Password:'),
                                          validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Change Password'))


class DeleteAccountForm(FlaskForm):
    """
        A form to request the deletion of a user's account. The CSRF token is used so that a user cannot be tricked
        to delete their profile by redirecting them to the URL.
    """

    submit = SubmitField(_l('Delete User Profile'),
                         description=_l('Delete your user profile and all data linked to it.'))

# endregion
