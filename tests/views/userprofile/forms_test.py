# -*- coding: utf-8 -*-

from unittest import TestCase

from flask_login import login_user
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import ValidationError

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.localization import get_language_names
from app.userprofile import User
from app.views.userprofile.forms import UniqueEmail
from app.views.userprofile.forms import UserSettingsForm


class UniqueEmailTest(TestCase):

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
            Test initializing the UniqueEmail validator with the default error message.

            Expected result: The default error message is used.
        """

        validator = UniqueEmail()
        self.assertEqual('The email address already is in use.', validator.message)

    def test_init_custom_message(self):
        """
            Test initializing the UniqueEmail validator with a custom error message.

            Expected result: The custom error message is used.
        """

        message = 'Another user already claims this email address.'
        validator = UniqueEmail(message=message)
        self.assertEqual(message, validator.message)

    def test_call_no_data(self):
        """
            Test the validator on an empty field.

            Expected result: No error is raised.
        """

        class UniqueEmailForm(FlaskForm):

            email = StringField('Email')

        form = UniqueEmailForm()
        validator = UniqueEmail()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.email)
        self.assertIsNone(validation)

    def test_call_unused_email(self):
        """
            Test the validator on a field with an unused email address.

            Expected result: No error is raised.
        """

        class UniqueEmailForm(FlaskForm):

            email = StringField('Email')

        form = UniqueEmailForm()
        form.email.data = 'test@example.com'
        validator = UniqueEmail()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.email)
        self.assertIsNone(validation)

    def test_call_email_of_current_user(self):
        """
            Test the validator on a field with the current user's email address.

            Expected result: No error is raised.
        """

        class UniqueEmailForm(FlaskForm):

            email = StringField('Email')

        # Create a test user.
        name = 'John Doe'
        email = 'test@example.com'
        user = User(email, name)
        db.session.add(user)
        db.session.commit()

        # Log in the test user.
        login_user(user)

        form = UniqueEmailForm()
        form.email.data = email
        validator = UniqueEmail()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.email)
        self.assertIsNone(validation)

    def test_call_email_of_different_user(self):
        """
            Test the validator on a field with a different user's email address.

            Expected result: An error is raised.
        """

        class UniqueEmailForm(FlaskForm):

            email = StringField('Email')

        # Create a test user.
        name = 'John Doe'
        email = 'test@example.com'
        user = User(email, name)
        db.session.add(user)
        db.session.commit()

        message = 'Another user already claims this email address.'
        form = UniqueEmailForm()
        form.email.data = email
        validator = UniqueEmail()

        with self.assertRaises(ValidationError) as thrown_message:
            # noinspection PyNoneFunctionAssignment
            validation = validator(form, form.email)
            self.assertIsNone(validation)
            self.assertEqual(message, thrown_message)


class UserSettingsFormTest(TestCase):

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

    def test_init(self):
        """
            Test that the form is correctly initialized.

            Expected result: The language field is initialized with the available languages.
        """

        languages = get_language_names(TestConfiguration.TRANSLATION_DIR)
        form = UserSettingsForm()
        self.assertListEqual(list(languages), form.language.choices)
