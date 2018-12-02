#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import ValidationError

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Role
from app.views.administration.forms import UniqueRoleName


class UniqueRoleNameTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def test_init_default_message(self):
        """
            Test initializing the UniqueRoleName validator with the default error message.

            Expected result: The default error message is used.
        """
        validator = UniqueRoleName()
        self.assertEqual('The role name already is in use.', validator.message)

    def test_init_custom_message(self):
        """
            Test initializing the UniqueRoleName validator with a custom error message.

            Expected result: The custom error message is used.
        """
        message = 'Another role already uses this name.'
        validator = UniqueRoleName(message=message)
        self.assertEqual(message, validator.message)

    def test_call_no_data(self):
        """
            Test the validator on an empty field.

            Expected result: No error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        form = UniqueRoleNameForm()
        validator = UniqueRoleName()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.name)
        self.assertIsNone(validation)

    def test_call_unused_name(self):
        """
            Test the validator on a field with an unused name.

            Expected result: No error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        form = UniqueRoleNameForm()
        form.name.data = 'Administrator'
        validator = UniqueRoleName()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.name)
        self.assertIsNone(validation)

    def test_call_name_of_current_role(self):
        """
            Test the validator on a field with the current role's name

            Expected result: No error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        # Create a test role.
        name = 'Administrator'
        role = Role(name=name)
        db.session.add(role)
        db.session.commit()

        form = UniqueRoleNameForm(obj=role)
        form.name.data = name
        validator = UniqueRoleName()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.name)
        self.assertIsNone(validation)

    def test_call_name_of_different_role(self):
        """
            Test the validator on a field with a different role's name.

            Expected result: An error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        # Create a test user.
        name = 'Administrator'
        role = Role(name=name)
        db.session.add(role)
        db.session.commit()

        message = 'Another role already uses this name.'
        form = UniqueRoleNameForm()
        form.name.data = name
        validator = UniqueRoleName()

        with self.assertRaises(ValidationError) as thrown_message:
            # noinspection PyNoneFunctionAssignment
            validation = validator(form, form.name)
            self.assertIsNone(validation)
            self.assertEqual(message, thrown_message)
