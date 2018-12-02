#!venv/bin/python
# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import Field
from wtforms import Form
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Length

from app.userprofile import Role

"""
    Forms and form related functionality for the user profile.
"""

# region Validators


class UniqueRoleName(object):
    """
        A WTForms validator to verify that an entered role name is not yet in use by another role.

        This validator requires the form to be initialized from an object if it is okay for the role name to stay
        the same.
    """

    def __init__(self, message=None) -> None:
        """
            Initialize the validator.

            :param message: The error message shown to the user if the validation fails.
        """
        if not message:
            message = _l('The role name already is in use.')

        self.message = message

    def __call__(self, form: Form, field: Field) -> None:
        """
            Execute the validator.

            :param form: The form to which the field belongs.
            :param field: The field to which this validator is assigned.
            :raise ValidationError: In case the validation fails.
        """
        name = field.data
        if not name:
            return

        # If
        if field.object_data == name:
            return

        # If there already is a role with that name and that role is not
        role = Role.load_from_name(name)
        if role:
            raise ValidationError(self.message)

# endregion

# region Forms


class RoleHeaderDataForm(FlaskForm):
    """
        A form to edit a role's header data.
    """

    name = StringField(_l('Name:'), validators=[DataRequired(), Length(max=255), UniqueRoleName()])
    submit = SubmitField(_l('Save'))

# endregion
