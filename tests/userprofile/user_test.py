#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from flask import url_for
from flask_login import current_user

from app import create_app
from app import db
from app import mail
from app.configuration import TestConfiguration
from app.exceptions import InvalidJWTokenPayloadError
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User
from app.userprofile import UserSettings
from app.userprofile.tokens import ChangeEmailAddressToken
from app.userprofile.tokens import DeleteAccountToken
from app.userprofile.tokens import ResetPasswordToken


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

    def test_role_none(self):
        """
            Test getting the user's role if the user does not have a role.

            Expected result: `None`
        """
        name = 'Jane Doe'
        email = 'test@example.com'
        user = User(email, name)

        self.assertIsNone(user._role_id)
        self.assertIsNone(user.role)

    def test_role_exists(self):
        """
            Test getting the user's role if the user has a role.

            Expected result: The role is returned.
        """
        role = Role(name='Administrator')

        name = 'Jane Doe'
        email = 'test@example.com'
        user = User(email, name)
        user.role = role

        db.session.add(role)
        db.session.add(user)
        db.session.commit()

        self.assertIsNotNone(role.id)
        self.assertIsNotNone(user._role_id)
        self.assertEqual(role.id, user._role_id)

        user = User.load_from_email(email)
        self.assertEqual(role, user.role)

    # endregion

    # region Initialization

    def test_init(self):
        """
            Test the user initialization.

            Expected result: The user is correctly initialized.
        """
        email = 'test@example.com'
        name = 'John Doe'

        with mail.record_messages() as outgoing:
            user = User(email, name)

            self.assertEqual(0, len(outgoing))

            self.assertIsNone(user.id)
            self.assertIsNone(user.password_hash)
            self.assertEqual(email, user.get_email())
            self.assertEqual(name, user.name)
            self.assertIsNone(user._is_activated)

            self.assertIsNotNone(user.settings)
            self.assertIsNone(user.settings._user_id)

            db.session.add(user)
            db.session.commit()

            self.assertEqual(1, user.id)
            self.assertTrue(user._is_activated)
            self.assertEqual(user.id, user.settings._user_id)

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
        self.assertEqual(email, loaded_user.get_email())
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
        self.assertEqual(email, loaded_user.get_email())
        self.assertEqual(name, loaded_user.name)

    def test_load_from_email_failure(self):
        """
            Test the from-email loader function with a non-existing user.

            Expected result: No user is returned.
        """
        loaded_user = User.load_from_email('test@example.com')
        self.assertIsNone(loaded_user)

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

    def test_login_failure_invalid_email(self):
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

    def test_login_failure_invalid_password(self):
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

        with mail.record_messages() as outgoing:
            changed_email = user.set_email(new_email)

            self.assertEqual(1, len(outgoing))
            self.assertListEqual([old_email], outgoing[0].recipients)
            self.assertIn('Your Email Address Has Been Changed', outgoing[0].subject)
            self.assertIn(f'Your email address has been changed to {new_email}', outgoing[0].body)
            self.assertIn(f'Your email address has been changed to ', outgoing[0].html)

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

        with mail.record_messages() as outgoing:
            changed_email = user.set_email(old_email)

            self.assertEqual(0, len(outgoing))
            self.assertTrue(changed_email)
            self.assertEqual(old_email, user.get_email())

    def test_set_email_success_no_old_email(self):
        """
            Test setting the user's email address if the user had none before.

            Expected result: The email address is set successfully, but no email is sent.
        """
        name = 'John Doe'
        # noinspection PyTypeChecker
        user = User(None, name)
        db.session.add(user)
        db.session.commit()

        email = 'test@example.com'
        with mail.record_messages() as outgoing:
            changed_email = user.set_email(email)

            self.assertEqual(0, len(outgoing))
            self.assertTrue(changed_email)
            self.assertEqual(email, user.get_email())

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

        with mail.record_messages() as outgoing:
            changed_email = user.set_email(existing_email)

            self.assertEqual(0, len(outgoing))
            self.assertFalse(changed_email)
            self.assertEqual(old_email, user.get_email())

    @patch('app.token.encode')
    def test_send_change_email_address_email(self, mock_encode: MagicMock):
        """
            Test sending a email address change email to the user.

            Expected result: An email with a link containing the token would be sent to the user.
        """
        # Fake a known token to be able to check for it in the mail.
        token_bytes = b'AFakeTokenForCheckingIfItIsIncludedInTheMail'
        token = token_bytes.decode('utf-8')
        mock_encode.return_value = token_bytes
        token_link = url_for('userprofile.change_email', token=token, _external=True)

        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        new_email = 'test2@example.com'
        with mail.record_messages() as outgoing:
            token_obj = user.send_change_email_address_email(new_email)
            validity_in_minutes = token_obj.get_validity(in_minutes=True)

            self.assertIsNotNone(token_obj)
            self.assertEqual(token, token_obj._token)
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

    def test_verify_change_email_address_token_success(self):
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
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user.id
        token_obj.new_email = new_email
        token = token_obj.create()

        loaded_user, loaded_email = User.verify_change_email_address_token(token)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user, loaded_user)
        self.assertEqual(new_email, loaded_email)

    def test_verify_change_email_address_token_invalid(self):
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
        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user.id
        token_obj.new_email = new_email
        token_obj.part_of_the_payload = True
        token = token_obj.create()

        with self.assertRaises(InvalidJWTokenPayloadError):
            loaded_user, loaded_email = User.verify_change_email_address_token(token)
            self.assertIsNone(loaded_user)
            self.assertIsNone(loaded_email)

    # endregion

    # region Password

    def test_set_password_success(self):
        """
            Test setting a new password if one has been set before.

            Expected result: The password is set on the user, but not in plaintext.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)
        user.set_password(password + '?')

        with mail.record_messages() as outgoing:
            user.set_password(password)

            self.assertEqual(1, len(outgoing))
            self.assertIn('Your Password Has Been Changed', outgoing[0].subject)
            self.assertListEqual([email], outgoing[0].recipients)
            self.assertIn('Your password has been updated.', outgoing[0].body)
            self.assertIn('Your password has been updated.', outgoing[0].html)
            self.assertIsNotNone(user.password_hash)
            self.assertNotEqual(password, user.password_hash)
            self.assertTrue(user.check_password(password))

    def test_set_password_success_first_password(self):
        """
            Test setting a new password if none has been set before.

            Expected result: The password is set on the user, but no mail is sent.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)

        self.assertIsNone(user.password_hash)

        with mail.record_messages() as outgoing:
            user.set_password(password)

            self.assertEqual(0, len(outgoing))
            self.assertIsNotNone(user.password_hash)
            self.assertTrue(user.check_password(password))

    def test_set_password_success_unchanged_password(self):
        """
            Test setting a new password, but set the same one as before.

            Expected result: The password is set on the user, but not in plaintext.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)

        user.set_password(password)
        self.assertTrue(user.check_password(password))

        with mail.record_messages() as outgoing:
            user.set_password(password)

            self.assertEqual(0, len(outgoing))
            self.assertIsNotNone(user.password_hash)
            self.assertTrue(user.check_password(password))

    def test_set_password_failure_no_password(self):
        """
            Test setting a new, empty password.

            Expected result: The password is not set on the user.
        """
        email = 'test@example.com'
        name = 'John Doe'
        password = None
        user = User(email, name)

        with mail.record_messages() as outgoing:
            # noinspection PyTypeChecker
            user.set_password(password)

            self.assertEqual(0, len(outgoing))
            self.assertIsNone(user.password_hash)
            # noinspection PyTypeChecker
            self.assertFalse(user.check_password(password))

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

    def test_check_password_failure_incorrect_password(self):
        """
            Test the password checking with an incorrect password.

            Expected result: The given password is incorrect and the result is False.
        """
        user = User('test@example.com', 'John Doe')
        user.set_password('Aerarium123!')

        is_correct = user.check_password('Aerarium456?')
        self.assertFalse(is_correct)

    def test_check_password_failure_no_set_password(self):
        """
            Test checking the password if the user has no password so far.

            Expected result: The result is False.
        """
        user = User('test@example.com', 'John Doe')
        is_correct = user.check_password('123456')
        self.assertFalse(is_correct)

    def test_check_password_failure_no_password(self):
        """
            Test checking the password if the user has no password so far.

            Expected result: The result is False.
        """
        user = User('test@example.com', 'John Doe')
        # noinspection PyTypeChecker
        is_correct = user.check_password(None)
        self.assertFalse(is_correct)

    @patch('app.token.encode')
    def test_send_password_reset_email_success(self, mock_encode: MagicMock):
        """
            Test sending a password reset email to the user.

            Expected result: An email with a link containing the token would be sent to the user.
        """
        # Fake a known token to be able to check for it in the mail.
        token_bytes = b'AFakeTokenForCheckingIfItIsIncludedInTheMail'
        token = token_bytes.decode('utf-8')
        mock_encode.return_value = token_bytes
        token_link = url_for('userprofile.reset_password', token=token, _external=True)

        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        with mail.record_messages() as outgoing:
            token_obj = user.send_password_reset_email()
            validity_in_minutes = token_obj.get_validity(in_minutes=True)

            self.assertIsNotNone(token_obj)
            self.assertEqual(token, token_obj._token)
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
        name = 'John Doe'
        # noinspection PyTypeChecker
        user = User(None, name)

        with mail.record_messages() as outgoing:
            user.send_password_reset_email()

            self.assertEqual(0, len(outgoing))

    def test_verify_password_reset_token_success(self):
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

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        loaded_user = User.verify_password_reset_token(token)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user, loaded_user)

    def test_verify_password_reset_token_failure_invalid(self):
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

        token_obj = ResetPasswordToken()
        token_obj.user_id = user_id
        token_obj.part_of_the_payload = True
        token = token_obj.create()

        with self.assertRaises(InvalidJWTokenPayloadError):
            loaded_user = User.verify_password_reset_token(token)
            self.assertIsNone(loaded_user)

    # endregion

    # region Delete

    @patch('app.token.encode')
    def test_send_delete_account_email(self, mock_encode: MagicMock):
        """
            Test sending a delete account email to the user.

            Expected result: An email with a link containing the token would be sent to the user.
        """
        # Fake a known token to be able to check for it in the mail.
        token_bytes = b'AFakeTokenForCheckingIfItIsIncludedInTheMail'
        token = token_bytes.decode('utf-8')
        mock_encode.return_value = token_bytes
        token_link = url_for('userprofile.delete_profile', token=token, _external=True)

        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        with mail.record_messages() as outgoing:
            token_obj = user.send_delete_account_email()
            validity_in_minutes = token_obj.get_validity(in_minutes=True)

            self.assertIsNotNone(token_obj)
            self.assertEqual(token, token_obj._token)
            self.assertEqual(1, len(outgoing))
            self.assertEqual([email], outgoing[0].recipients)
            self.assertIn('Delete Your User Profile', outgoing[0].subject)
            self.assertIn(token_link, outgoing[0].body)
            self.assertIn(token_link, outgoing[0].html)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].body)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].html)

    def test_verify_delete_account_token_success(self):
        """
            Test the delete account JWT without any failure.

            Expected result: The token returns the correct user when verifying.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        token_obj = DeleteAccountToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        loaded_user = User.verify_delete_account_token(token)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user, loaded_user)

    def test_verify_delete_account_token_invalid(self):
        """
            Test the delete account JWT without any failure.

            Expected result: The token does not return a user when verifying.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        token_obj = DeleteAccountToken()
        token_obj.user_id = user.id
        token_obj.part_of_the_payload = True
        token = token_obj.create()

        with self.assertRaises(InvalidJWTokenPayloadError):
            loaded_user = User.verify_delete_account_token(token)
            self.assertIsNotNone(loaded_user)

    def test_delete_logged_in(self):
        """
            Test deleting the user when they are logged in.

            Expected result: The user is logged out, informed via mail, and deleted. Other users are not deleted.
        """
        other_email = 'info@example.com'
        other_name = 'Jane Doe'
        other_user = User(other_email, other_name)
        db.session.add(other_user)

        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user = User.login(email, password)
        other_id = other_user.id
        user_id = user.id

        self.assertEqual(current_user, user)

        with mail.record_messages() as outgoing:
            user.delete()

            # Test that the user has been logged out.
            self.assertNotEqual(current_user, user)

            # Test that an email has been sent.
            self.assertEqual(1, len(outgoing))
            self.assertListEqual([email], outgoing[0].recipients)
            self.assertIn('Your User Profile Has Been Deleted', outgoing[0].subject)

            # Test that the user has actually been deleted.
            loaded_user = User.load_from_id(user_id)
            self.assertIsNone(loaded_user)

            # Test that other users have not been deleted.
            loaded_user = User.load_from_id(other_id)
            self.assertEqual(other_user, loaded_user)

            # Test that the user's data has been deleted from other tables as well.
            settings = UserSettings.query.get(user_id)
            self.assertIsNone(settings)

    def test_delete_logged_out(self):
        """
            Test deleting the user when they are logged out.

            Expected result: The user is informed via mail and deleted. Other users are not deleted.
        """
        other_email = 'info@example.com'
        other_name = 'Jane Doe'
        other_password = 'Aerarium123!'
        other_user = User(other_email, other_name)
        other_user.set_password(other_password)
        db.session.add(other_user)

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        other_user = User.login(other_email, other_password)
        other_id = other_user.id
        user_id = user.id

        self.assertEqual(current_user, other_user)

        with mail.record_messages() as outgoing:
            user.delete()

            # Test that the other user has not been logged out.
            self.assertEqual(current_user, other_user)

            # Test that an email has been sent.
            self.assertEqual(1, len(outgoing))
            self.assertListEqual([email], outgoing[0].recipients)
            self.assertIn('Your User Profile Has Been Deleted', outgoing[0].subject)

            # Test that the user has actually been deleted.
            loaded_user = User.load_from_id(user_id)
            self.assertIsNone(loaded_user)

            # Test that other users have not been deleted.
            loaded_user = User.load_from_id(other_id)
            self.assertEqual(other_user, loaded_user)

            # Test that the user's data has been deleted from other tables as well.
            settings = UserSettings.query.get(user_id)
            self.assertIsNone(settings)

    # endregion

    # region Permissions

    def test_current_user_has_permissions_all_no_role(self):
        """
            Test the `current_user_has_permissions_all` method if the user does not have a role.

            Expected result: `False`
        """

        # Ensure the user has no role.
        self.assertFalse(hasattr(current_user, 'role'))

        self.assertFalse(User.current_user_has_permissions_all(Permission.EditRole))

    def test_current_user_has_permissions_all_no_permission(self):
        """
            Test the `current_user_has_permissions_all` method if the user does not have the requested permission.

            Expected result: `False`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role()

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        self.assertFalse(user.role.has_permissions_all(permission))

        self.assertFalse(User.current_user_has_permissions_all(permission))

    def test_current_user_has_permissions_all_with_permission(self):
        """
            Test the `current_user_has_permissions_all` method if the user has the requested permission.

            Expected result: `True`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role()

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.add_permissions(permission)

        self.assertTrue(user.role.has_permission(permission))

        self.assertTrue(User.current_user_has_permissions_all(permission))

    def test_current_user_has_permissions_all_with_multiple_permissions(self):
        """
            Test the `current_user_has_permissions_all` method if the user has the requested permissions.

            Expected result: `True`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role()

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        user.role.add_permissions(Permission.EditRole, Permission.EditUser)

        self.assertTrue(user.role.has_permissions_all(Permission.EditRole, Permission.EditUser))

        self.assertTrue(User.current_user_has_permissions_all(Permission.EditRole, Permission.EditUser))

    def test_current_user_has_permissions_one_of_no_role_attribute(self):
        """
            Test the `current_user_has_permissions_one_of` method if the user does not have a role attribute.

            Expected result: `False`
        """

        # Ensure the user has no role.
        self.assertFalse(hasattr(current_user, 'role'))

        self.assertFalse(User.current_user_has_permissions_one_of(Permission.EditRole))

    def test_current_user_has_permissions_one_of_no_role(self):
        """
            Test the `current_user_has_permissions_one_of` method if the user does not have a role.

            Expected result: `False`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        self.assertFalse(User.current_user_has_permissions_one_of(permission))

    def test_current_user_has_permissions_one_of_no_permission(self):
        """
            Test the `current_user_has_permissions_one_of` method if the user does not have the requested permission.

            Expected result: `False`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role()

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        self.assertFalse(user.role.has_permissions_all(permission))

        self.assertFalse(User.current_user_has_permissions_one_of(permission))

    def test_current_user_has_permissions_one_of_with_permission(self):
        """
            Test the `current_user_has_permissions_one_of` method if the user has the requested permission.

            Expected result: `True`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role()

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.add_permissions(permission)

        self.assertTrue(user.role.has_permissions_all(permission))

        self.assertTrue(User.current_user_has_permissions_one_of(permission))
        self.assertFalse(User.current_user_has_permissions_one_of(Permission.EditGlobalSettings))

    def test_current_user_has_permissions_one_of_with_multiple_permissions(self):
        """
            Test the `current_user_has_permissions_one_of` method if the user has on of the requested permission.

            Expected result: `True`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role()

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.add_permissions(permission)

        self.assertTrue(user.role.has_permission(permission))

        self.assertTrue(User.current_user_has_permissions_one_of(Permission.EditRole, Permission.EditUser))
        self.assertFalse(User.current_user_has_permissions_one_of(Permission.EditGlobalSettings, Permission.EditUser))

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
