#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_wtf import FlaskForm
from werkzeug.wrappers import Response
from wtforms import StringField
from wtforms import ValidationError

from app import create_app
from app import db
from app import mail
from app.authorization import logout_required
from app.authorization import User
from app.authorization.user import UniqueEmail
from app.configuration import TestConfiguration
from app.token import get_token
from app.token import get_validity


class UserTest(TestCase):

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

    # region Fields and Properties

    def test_is_active_get(self):
        """
            Test getting the account's activation status.

            Expected result: The ``is_active`` property returns the value of the ``is_activated`` field.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        self.assertIsNone(user.is_active)

        user._is_activated = True
        self.assertTrue(user.is_active)

        user._is_activated = False
        self.assertFalse(user.is_active)

    def test_is_active_set(self):
        """
            Test setting the account's activation status.

            Expected result: The ``is_active`` property sets the value of the ``is_activated`` field.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)
        self.assertIsNone(user._is_activated)

        user.is_active = True
        self.assertTrue(user._is_activated)

        user.is_active = False
        self.assertFalse(user._is_activated)

    # endregion

    # region Initialization

    def test_init(self):
        """
            Test the user initialization.

            Expected result: The user is correctly initialized.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        self.assertIsNone(user.id)
        self.assertIsNone(user.password_hash)
        self.assertEqual(email, user._email)
        self.assertEqual(name, user.name)
        self.assertIsNone(user._is_activated)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(1, user.id)
        self.assertTrue(user._is_activated)

    def test_load_from_id_success(self):
        """
            Test the user loader function with an existing user.

            Expected result: The user with the given ID is returned.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        loaded_user = User.load_from_id(user_id)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user_id, loaded_user.id)
        self.assertEqual(email, loaded_user._email)
        self.assertEqual(name, loaded_user.name)

    def test_load_from_id_failure(self):
        """
            Test the user loader function with a non-existing user.

            Expected result: No user is returned.
        """
        loaded_user = User.load_from_id(1)
        self.assertIsNone(loaded_user)

    def test_load_from_email_success(self):
        """
            Test the from-email loader function with an existing user.

            Expected result: The user with the given email address is returned.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        loaded_user = User.load_from_email(email)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user_id, loaded_user.id)
        self.assertEqual(email, loaded_user._email)
        self.assertEqual(name, loaded_user.name)

    def test_load_from_email_failure(self):
        """
            Test the from-email loader function with a non-existing user.

            Expected result: No user is returned.
        """
        loaded_user = User.load_from_email('test@example.com')
        self.assertIsNone(loaded_user)

    # endregion

    # region Email

    def test_get_email(self):
        """
            Test getting the email.

            Expected result: The user's email address is returned.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)
        self.assertEqual(email, user.get_email())

    def test_set_email_success(self):
        """
            Test setting the user's email address to a new one that is not yet in use.

            Expected result: The email address is set successfully.
        """
        old_email = 'test@example.com'
        new_email = 'test2@example.com'
        name = 'John Doe'
        user = User(old_email, name)
        db.session.add(user)
        db.session.commit()

        changed_email = user.set_email(new_email)
        self.assertTrue(changed_email)
        self.assertEqual(new_email, user.get_email())

    def test_set_email_success_unchanged(self):
        """
            Test setting the user's email address to the user's current one.

            Expected result: The email address is set successfully.
        """
        old_email = 'test@example.com'
        name = 'John Doe'
        user = User(old_email, name)
        db.session.add(user)
        db.session.commit()

        changed_email = user.set_email(old_email)
        self.assertTrue(changed_email)
        self.assertEqual(old_email, user.get_email())

    def test_set_email_failure(self):
        """
            Test setting the user's email address to a new one that already is in use.

            Expected result: The email address is not changed.
        """
        existing_email = 'test2@example.com'
        existing_name = 'Jane Doe'
        existing_user = User(existing_email, existing_name)

        old_email = 'test@example.com'
        name = 'John Doe'
        user = User(old_email, name)

        db.session.add(existing_user)
        db.session.add(user)
        db.session.commit()

        changed_email = user.set_email(existing_email)
        self.assertFalse(changed_email)
        self.assertEqual(old_email, user.get_email())

    def test_change_email_address_token_success(self):
        """
            Test the email address change JWT without any failure.

            Expected result: The token is generated and returns the correct user and new email address when verifying.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        new_email = 'test2@example.com'
        token = user._get_change_email_address_token(new_email)
        self.assertIsNotNone(token)

        loaded_user, loaded_email = User.verify_change_email_address_token(token)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user, loaded_user)
        self.assertEqual(new_email, loaded_email)

    def test_change_email_address_token_invalid(self):
        """
            Test the email address change JWT without any failure.

            Expected result: The token is generated and returns the correct user and new email address when verifying.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        new_email = 'test2@example.com'
        token = user._get_change_email_address_token(new_email)
        self.assertIsNotNone(token)

        loaded_user, loaded_email = User.verify_change_email_address_token('invalid' + token)
        self.assertIsNone(loaded_user)
        self.assertIsNone(loaded_email)

    def test_change_email_address_token_not_email_address_change(self):
        """
            Test the email address change JWT with a token that is not intended for changing email address.

            Expected result: The token does not return a user when verifying.
        """
        token = get_token(forge_tests=True)

        loaded_user, loaded_email = User.verify_change_email_address_token(token)
        self.assertIsNone(loaded_user)
        self.assertIsNone(loaded_email)

    @patch('app.authorization.user.get_token')
    def test_send_change_email_address_email_success(self, mock_get_token: MagicMock):
        """
            Test sending a email address change email to the user.

            Expected result: An email with a link containing the token would be sent to the user.
        """
        # Fake a known token to be able to check for it in the mail.
        token = 'AFakeTokenForCheckingIfItIsIncludedInTheMail'
        mock_get_token.return_value = token
        token_link = url_for('authorization.change_email', token=token, _external=True)

        # Use a defined validity to check it is included in the mail.
        validity_in_minutes = get_validity(in_minutes=True)

        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        new_email = 'test2@example.com'
        with mail.record_messages() as outgoing:
            user.send_change_email_address_email(new_email)

            self.assertEqual(1, len(outgoing))
            self.assertEqual([new_email], outgoing[0].recipients)
            self.assertIn('Change Your Email Address', outgoing[0].subject)
            self.assertIn(token_link, outgoing[0].body)
            self.assertIn(token_link, outgoing[0].html)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].body)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].html)
            self.assertIn(f'from {email}', outgoing[0].body)
            self.assertIn(f'to {new_email}', outgoing[0].body)
            self.assertIn(f'{email}', outgoing[0].html)
            self.assertIn(f'{new_email}', outgoing[0].html)

    @patch('app.authorization.user.get_token')
    def test_send_change_email_address_email_failure_no_token(self, mock_get_token: MagicMock):
        """
            Test sending a email address change email to the user if generating a token fails.

            Expected result: No email would be sent.
        """
        mock_get_token.return_value = None

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        new_email = 'test2@example.com'
        with mail.record_messages() as outgoing:
            user.send_change_email_address_email(new_email)

            self.assertEqual(0, len(outgoing))

    # endregion

    # region Password

    def test_set_password(self):
        """
            Test the password setting.

            Expected result: The password is set on the user, but not in plaintext.
        """
        password = 'Aerarium123!'
        user = User('test@example.com', 'John Doe')

        self.assertIsNone(user.password_hash)

        user.set_password(password)
        self.assertIsNotNone(user.password_hash)
        self.assertNotEqual(password, user.password_hash)

    def test_check_password_success(self):
        """
            Test the password checking with the correct password.

            Expected result: The given password is correct and the result is True.
        """
        password = 'Aerarium123!'
        user = User('test@example.com', 'John Doe')
        user.set_password(password)

        is_correct = user.check_password(password)
        self.assertTrue(is_correct)

    def test_check_password_failure(self):
        """
            Test the password checking with an incorrect password.

            Expected result: The given password is incorrect and the result is False.
        """
        user = User('test@example.com', 'John Doe')
        user.set_password('Aerarium123!')

        is_correct = user.check_password('Aerarium456?')
        self.assertFalse(is_correct)

    def test_password_reset_token_success(self):
        """
            Test the password reset JWT without any failures.

            Expected result: The token is generated and returns the correct user when verifying.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        loaded_user = User.verify_password_reset_token(token)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user, loaded_user)

    def test_password_reset_token_failure_invalid(self):
        """
            Test the password reset JWT with an invalid token.

            Expected result: The token is generated, but does not return a user when verifying.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        token = user._get_password_reset_token()
        self.assertIsNotNone(token)

        loaded_user = User.verify_password_reset_token('invalid' + token)
        self.assertIsNone(loaded_user)

    def test_password_reset_token_failure_not_password_reset(self):
        """
            Test the password reset JWT with a token that is not intended for resetting passwords.

            Expected result: The token is generated, but does not return a user when verifying.
        """
        token = get_token(forge_tests=True)

        loaded_user = User.verify_password_reset_token(token)
        self.assertIsNone(loaded_user)

    @patch('app.authorization.user.get_token')
    def test_send_password_reset_email_success(self, mock_get_token: MagicMock):
        """
            Test sending a password reset email to the user.

            Expected result: An email with a link containing the token would be sent to the user.
        """
        # Fake a known token to be able to check for it in the mail.
        token = 'AFakeTokenForCheckingIfItIsIncludedInTheMail'
        mock_get_token.return_value = token
        token_link = url_for('authorization.reset_password', token=token, _external=True)

        # Use a defined validity to check it is included in the mail.
        validity_in_minutes = get_validity(in_minutes=True)

        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        with mail.record_messages() as outgoing:
            user.send_password_reset_email()

            self.assertEqual(1, len(outgoing))
            self.assertEqual([user.get_email()], outgoing[0].recipients)
            self.assertIn('Reset Your Password', outgoing[0].subject)
            self.assertIn(token_link, outgoing[0].body)
            self.assertIn(token_link, outgoing[0].html)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].body)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].html)

    def test_send_password_reset_email_failure_no_email(self):
        """
            Test sending a password reset email to the user if the user has no email address.

            Expected result: No email would be sent.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)
        user._email = None

        with mail.record_messages() as outgoing:
            user.send_password_reset_email()

            self.assertEqual(0, len(outgoing))

    @patch('app.authorization.user.get_token')
    def test_send_password_reset_email_failure_no_token(self, mock_get_token: MagicMock):
        """
            Test sending a password reset email to the user if generating a token fails.

            Expected result: No email would be sent.
        """
        mock_get_token.return_value = None

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        with mail.record_messages() as outgoing:
            user.send_password_reset_email()

            self.assertEqual(0, len(outgoing))

    # endregion

    # region Login/Logout

    def test_login_success(self):
        """
            Test logging in a user with valid credentials.

            Expected result: The user is successfully logged in and returned.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)
        self.assertTrue(user.is_active)

        logged_in_user = User.login(email, password)
        self.assertIsNotNone(logged_in_user)
        self.assertEqual(logged_in_user, current_user)
        self.assertEqual(logged_in_user.id, user_id)
        self.assertTrue(current_user.is_authenticated)

    def test_login_failure_email(self):
        """
            Test logging in a user with an invalid email address.

            Expected result: The user is not logged in.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)
        self.assertTrue(user.is_active)

        logged_in_user = User.login('invalid-' + email, password)
        self.assertIsNone(logged_in_user)
        self.assertNotEqual(current_user.get_id(), user_id)
        self.assertFalse(current_user.is_authenticated)

    def test_login_failure_password(self):
        """
            Test logging in a user with an invalid password.

            Expected result: The user is not logged in.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)
        self.assertTrue(user.is_active)

        logged_in_user = User.login(email, 'invalid-' + password)
        self.assertIsNone(logged_in_user)
        self.assertNotEqual(current_user.get_id(), user_id)
        self.assertFalse(current_user.is_authenticated)

    def test_login_failure_not_activated(self):
        """
            Test logging in a user with valid credentials but whose account is not activated.

            Expected result: The user is not logged in.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)
        user.is_active = False

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)
        self.assertFalse(user.is_active)

        logged_in_user = User.login(email, password)
        self.assertIsNone(logged_in_user)
        self.assertNotEqual(current_user.get_id(), user_id)
        self.assertFalse(current_user.is_authenticated)

    def test_logout(self):
        """
            Test logging out a user.

            Expected result: The user is no longer logged in.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        User.login(email, password)
        self.assertTrue(current_user.is_authenticated)

        logged_out = User.logout()
        self.assertTrue(logged_out)
        self.assertFalse(current_user.is_authenticated)
        self.assertNotEqual(current_user.get_id(), user_id)

    # endregion

    # region System

    def test_repr(self):
        """
            Test the string representation of the user.

            Expected result: The representation contains details on the user.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        self.assertEqual(f'<User [None] {email}>', str(user))

        db.session.add(user)
        db.session.commit()

        self.assertEqual(f'<User [1] {email}>', str(user))

    # endregion

    # region Decorators

    def test_logout_required_logged_out(self):
        """
            Test the ``logout_required`` decorator with an anonymous user.

            Expected result: The decorated view function is returned.
        """

        def test_view_function() -> str:
            """
                A simple test "view" function.

                :return: 'Decorated View'.
            """
            return 'Decorated View'

        view_function = logout_required(test_view_function)
        response = view_function()
        self.assertEqual('Decorated View', response)

    def test_logout_required_logged_in(self):
        """
            Test the ``logout_required`` decorator with a logged-in user.

            Expected result: The redirect response to the home page is returned.
        """

        def test_view_function() -> str:
            """
                A simple test "view" function.

                :return: 'Decorated View'.
            """
            return 'Decorated View'

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()
        login_user(user)

        redirect_function = logout_required(test_view_function)
        response = redirect_function()
        self.assertIsInstance(response, Response)
        self.assertEqual(302, response.status_code)
        self.assertEqual(url_for('main.index'), response.location)

    # endregion

    # region Forms

    def test_unique_email_init_default_message(self):
        """
            Test initializing the UniqueEmail validator with the default error message.

            Expected result: The default error message is used.
        """
        validator = UniqueEmail()
        self.assertEqual('The email address already is in use.', validator.message)

    def test_unique_email_init_custom_message(self):
        """
            Test initializing the UniqueEmail validator with a custom error message.

            Expected result: The custom error message is used.
        """
        message = 'Another user already claims this email address.'
        validator = UniqueEmail(message=message)
        self.assertEqual(message, validator.message)

    def test_unique_email_call_no_data(self):
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

    def test_unique_email_call_unused_email(self):
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

    def test_unique_email_call_email_of_current_user(self):
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

    def test_unique_email_call_email_of_different_user(self):
        """
            Test the validator on a field with a different user's email address.

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

        message = 'Another user already claims this email address.'
        form = UniqueEmailForm()
        form.email.data = email
        validator = UniqueEmail()

        with self.assertRaises(ValidationError) as thrown_message:
            # noinspection PyNoneFunctionAssignment
            validation = validator(form, form.email)
            self.assertIsNone(validation)
            self.assertEqual(message, thrown_message)

    # endregion
