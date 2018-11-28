#!venv/bin/python
# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as _l
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import Field
from wtforms import Form
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Email as IsEmail
from wtforms.validators import EqualTo

from app.configuration import BaseConfiguration
from app.localization import get_language_names
from app.userprofile import User

# region Validators


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

# endregion

# region Forms


class DeleteUserProfileForm(FlaskForm):
    """
        A form to request the deletion of a user's profile. The CSRF token is used so that a user cannot be tricked
        to delete their profile by redirecting them to the URL.
    """

    submit = SubmitField(_l('Delete User Profile'),
                         description=_l('Delete your user profile and all data linked to it.'))


class EmailForm(FlaskForm):
    """
        A form requesting a user to enter their email address.
    """

    email = StringField(_l('Email:'), validators=[DataRequired(), IsEmail()])
    submit = SubmitField(_l('Submit'))


class LoginForm(FlaskForm):
    """
        A form allowing a user to log in.
    """

    email = StringField(_l('Email:'), validators=[DataRequired(), IsEmail()])
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


class UserProfileForm(FlaskForm):
    """
        A form allowing a user to change their profile.
    """
    name = StringField(_l('Name:'), validators=[DataRequired()])
    email = StringField(_l('Email:'), validators=[DataRequired(), IsEmail(), UniqueEmail()],
                        description=_l('We will send you an email to your new address with a link to confirm the \
                                        changes. The email address will not be changed until you confirm this action.'))
    password = PasswordField(_l('New Password:'),
                             description=_l('Leave this field empty if you do not want to change your password.'))
    password_confirmation = PasswordField(_l('Confirm Your New Password:'), validators=[EqualTo('password')])
    submit = SubmitField(_l('Save'))


class UserSettingsForm(FlaskForm):
    """
        A form for changing a user's settings.
    """
    language = SelectField(_l('Language:'), validators=[DataRequired()],
                           description=_l('The language in which you want to use the application.'))
    submit = SubmitField(_l('Save'))

    def __init__(self, *args, **kwargs) -> None:
        """

            :param args:
            :param kwargs:
        """
        super().__init__(*args, **kwargs)

        self.language.choices = get_language_names(BaseConfiguration.TRANSLATION_DIR)

# endregion
