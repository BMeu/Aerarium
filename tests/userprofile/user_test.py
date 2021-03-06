# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from flask import url_for
from flask_easyjwt import EasyJWTError
from flask_login import current_user

from app import create_app
from app import db
from app import mail
from app import timedelta_to_minutes
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User
from app.userprofile import UserPagination
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

    def test_email(self):
        """
            Test getting the email.

            Expected result: The user's email address is returned.
        """

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)
        self.assertEqual(email, user.email)

    def test_is_active_get(self):
        """
            Test getting the account's activation status.

            Expected result: The `is_active` property returns the value of the `is_activated` field.
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

            Expected result: The `is_active` property sets the value of the `is_activated` field.
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
            self.assertIsNone(user._password_hash)
            self.assertEqual(email, user.email)
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
        self.assertEqual(email, loaded_user.email)
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
        self.assertEqual(email, loaded_user.email)
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

    def test_refresh_login_no_user(self):
        """
            Test refreshing the login if no user is logged in.

            Expected result: Nothing happens.
        """

        password = '123456'
        user = User.refresh_login(password)

        self.assertIsNone(user)

    def test_refresh_login_wrong_password(self):
        """
            Test refreshing the login with a wrong password.

            Expected result: The user is not logged in.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        user = User.refresh_login('invalid' + password)
        self.assertIsNone(user)

    def test_refresh_login_success(self):
        """
            Test refreshing the login with a wrong password.

            Expected result: The user is not logged in.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user_id = user.id
        user.login(email, password)

        user = User.refresh_login(password)
        self.assertIsNotNone(user)
        self.assertEqual(user_id, user.id)

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
            changed_email = user._set_email(new_email)

            self.assertEqual(1, len(outgoing))
            self.assertListEqual([old_email], outgoing[0].recipients)
            self.assertIn('Your Email Address Has Been Changed', outgoing[0].subject)
            self.assertIn(f'Your email address has been changed to {new_email}', outgoing[0].body)
            self.assertIn('Your email address has been changed to ', outgoing[0].html)

            self.assertTrue(changed_email)
            self.assertEqual(new_email, user.email)

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
            changed_email = user._set_email(old_email)

            self.assertEqual(0, len(outgoing))
            self.assertTrue(changed_email)
            self.assertEqual(old_email, user.email)

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
            changed_email = user._set_email(email)

            self.assertEqual(0, len(outgoing))
            self.assertTrue(changed_email)
            self.assertEqual(email, user.email)

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
            changed_email = user._set_email(existing_email)

            self.assertEqual(0, len(outgoing))
            self.assertFalse(changed_email)
            self.assertEqual(old_email, user.email)

    @patch('easyjwt.easyjwt.jwt_encode')
    def test_request_email_address_change(self, mock_encode: MagicMock):
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
            validity = user.request_email_address_change(new_email)
            validity_in_minutes = timedelta_to_minutes(validity)

            self.assertIsNotNone(validity)
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

    def test_set_email_address_from_token_failure_duplicate_email_address(self):
        """
            Test setting a duplicate email address from a token.

            Expected result: The email address is not changed.
        """

        email_user1 = 'test@example.com'
        name_user1 = 'John Doe'
        user1 = User(email_user1, name_user1)
        db.session.add(user1)

        email_user2 = 'test2@example.com'
        name_user2 = 'Jane Doe'
        user2 = User(email_user2, name_user2)
        db.session.add(user2)

        db.session.commit()

        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = user1.id
        token_obj.new_email = email_user2
        token = token_obj.create()

        changed = User.set_email_address_from_token(token)
        self.assertFalse(changed)
        self.assertEqual(user1, User.load_from_email(email_user1))
        self.assertEqual(user2, User.load_from_email(email_user2))

    def test_set_email_address_from_token_failure_invalid_token(self):
        """
            Test setting the email address from a token with an invalid token.

            Expected result: An `EasyJWTError` is raised.
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

        with self.assertRaises(EasyJWTError):
            User.set_email_address_from_token(token)

        self.assertIsNone(User.load_from_email(new_email))

    def test_set_email_address_from_token_failure_invalid_user(self):
        """
            Test setting the email address from a token for an unknown user.

            Expected result: A `ValueError` is raised.
        """

        new_email = 'test2@example.com'

        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = 42
        token_obj.new_email = new_email
        token = token_obj.create()

        with self.assertRaises(ValueError) as exception_cm:
            User.set_email_address_from_token(token)

        self.assertIsNone(User.load_from_email(new_email))
        self.assertEqual('User 42 does not exist', str(exception_cm.exception))

    def test_set_email_address_from_token_success(self):
        """
            Test setting the email address from a token without any failure.

            Expected result: The email address is changed.
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

        changed = User.set_email_address_from_token(token)
        self.assertTrue(changed)
        self.assertEqual(user, User.load_from_email(new_email))

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
            self.assertIsNotNone(user._password_hash)
            self.assertNotEqual(password, user._password_hash)
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

        self.assertIsNone(user._password_hash)

        with mail.record_messages() as outgoing:
            user.set_password(password)

            self.assertEqual(0, len(outgoing))
            self.assertIsNotNone(user._password_hash)
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
            self.assertIsNotNone(user._password_hash)
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
            self.assertIsNone(user._password_hash)
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

    @patch('easyjwt.easyjwt.jwt_encode')
    def test_request_password_reset_success(self, mock_encode: MagicMock):
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
            token_obj = user.request_password_reset()
            validity_in_minutes = timedelta_to_minutes(token_obj.get_validity())

            self.assertIsNotNone(token_obj)
            self.assertEqual(1, len(outgoing))
            self.assertEqual([user.email], outgoing[0].recipients)
            self.assertIn('Reset Your Password', outgoing[0].subject)
            self.assertIn(token_link, outgoing[0].body)
            self.assertIn(token_link, outgoing[0].html)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].body)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].html)

    def test_request_password_reset_failure_no_email(self):
        """
            Test sending a password reset email to the user if the user has no email address.

            Expected result: No email would be sent.
        """

        name = 'John Doe'
        # noinspection PyTypeChecker
        user = User(None, name)

        with mail.record_messages() as outgoing:
            user.request_password_reset()

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

        loaded_user = User.verify_password_reset_token(token)
        self.assertIsNone(loaded_user)

    # endregion

    # region Delete

    @patch('easyjwt.easyjwt.jwt_encode')
    def test_request_account_deletion_success(self, mock_encode: MagicMock):
        """
            Test sending a delete account email to the user if they have an email address.

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
            token_obj = user.request_account_deletion()
            validity_in_minutes = timedelta_to_minutes(token_obj.get_validity())

            self.assertIsNotNone(token_obj)
            self.assertEqual(1, len(outgoing))
            self.assertEqual([email], outgoing[0].recipients)
            self.assertIn('Delete Your User Profile', outgoing[0].subject)
            self.assertIn(token_link, outgoing[0].body)
            self.assertIn(token_link, outgoing[0].html)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].body)
            self.assertIn(f'{validity_in_minutes} minutes', outgoing[0].html)

    def test_request_account_deletion_failure(self):
        """
            Test sending a delete account email to the user if they have no email address.

            Expected result: No email would be sent.
        """

        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)
        user._email = None

        with mail.record_messages() as outgoing:
            token_obj = user.request_account_deletion()

            self.assertIsNone(token_obj)
            self.assertEqual(0, len(outgoing))

    def test_delete_account_from_token_success(self):
        """
            Test deleting the currently logged in user's account from a token.

            Expected result: The user is deleted.
        """

        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user = User.login(email, password)
        user_id = user.id

        token_obj = DeleteAccountToken()
        token_obj.user_id = user_id
        token = token_obj.create()

        deleted = User.delete_account_from_token(token)
        self.assertTrue(deleted)
        self.assertIsNone(User.load_from_id(user_id))

    def test_delete_account_from_token_failure_other_user_logged_in(self):
        """
            Test deleting a user's account from a token if a different user is logged in.

            Expected result: Neither of the two users is deleted.
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

        token_obj = DeleteAccountToken()
        token_obj.user_id = user.id
        token = token_obj.create()

        deleted = User.delete_account_from_token(token)
        self.assertFalse(deleted)
        self.assertIsNotNone(User.load_from_id(user.id))
        self.assertIsNotNone(User.load_from_id(other_user.id))

    def test_delete_account_from_token_failure_unknown_user_id(self):
        """
            Test deleting the currently logged in user's account from a token that has an unknown user ID.

            Expected result: The user is not deleted.
        """

        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user = User.login(email, password)

        invalid_id = user.id + 1
        self.assertIsNone(User.load_from_id(invalid_id))

        token_obj = DeleteAccountToken()
        token_obj.user_id = invalid_id
        token = token_obj.create()

        deleted = User.delete_account_from_token(token)
        self.assertFalse(deleted)
        self.assertIsNotNone(User.load_from_id(user.id))

    def test_delete_account_from_token_failure_invalid_token(self):
        """
            Test deleting the currently logged in user's account from a token that is invalid.

            Expected result: The user is not deleted.
        """

        email = 'test@example.com'
        name = 'John Doe'
        password = 'Aerarium123!'
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user = User.login(email, password)

        token_obj = DeleteAccountToken()
        token_obj.user_id = user.id
        token_obj._easyjwt_class = 'InvalidClass'
        token = token_obj.create()

        deleted = User.delete_account_from_token(token)
        self.assertFalse(deleted)
        self.assertIsNotNone(User.load_from_id(user.id))

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
            user._delete()

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
            user._delete()

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

    def test_delete_no_email(self):
        """
            Test deleting the user when they are logged in and have not set an email address.

            Expected result: The user is logged out and deleted. Other users are not deleted.
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

        user._email = None

        with mail.record_messages() as outgoing:
            user._delete()

            # Test that the user has been logged out.
            self.assertNotEqual(current_user, user)

            # Test that no email has been sent.
            self.assertEqual(0, len(outgoing))

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

    def test_current_user_has_permission_no_role(self):
        """
            Test the `current_user_has_permission` method if the user does not have a role.

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

        self.assertFalse(User.current_user_has_permission(Permission.EditRole))

    def test_current_user_has_permission_no_permission(self):
        """
            Test the `current_user_has_permission` method if the user does not have the requested permission.

            Expected result: `False`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role('Administrator')

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        self.assertFalse(User.current_user_has_permission(permission))

    def test_current_user_has_permission_with_permission(self):
        """
            Test the `current_user_has_permission` method if the user has the requested permission.

            Expected result: `True`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role('Administrator')

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.permissions = permission

        self.assertTrue(user.role.has_permission(permission))
        self.assertTrue(User.current_user_has_permission(permission))

    def test_current_user_has_permissions_all_no_role(self):
        """
            Test the `current_user_has_permissions_all` method if the user does not have a role.

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
        user.role = Role('Administrator')

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
        user.role = Role('Administrator')

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.permissions = permission

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
        user.role = Role('Administrator')

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        user.role.permissions = Permission.EditRole | Permission.EditUser

        self.assertTrue(user.role.has_permissions_all(Permission.EditRole, Permission.EditUser))
        self.assertTrue(User.current_user_has_permissions_all(Permission.EditRole, Permission.EditUser))

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
        user.role = Role('Administrator')

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
        user.role = Role('Administrator')

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.permissions = permission

        self.assertTrue(user.role.has_permissions_all(permission))
        self.assertTrue(User.current_user_has_permissions_one_of(permission))
        self.assertFalse(User.current_user_has_permissions_one_of(Permission.EditGlobalSettings))

    def test_current_user_has_permissions_one_of_with_multiple_permissions(self):
        """
            Test the `current_user_has_permissions_one_of` method if the user has one of the requested permission.

            Expected result: `True`
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role('Administrator')

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        permission = Permission.EditRole
        user.role.permissions = permission

        self.assertTrue(user.role.has_permission(permission))
        self.assertTrue(User.current_user_has_permissions_one_of(Permission.EditRole, Permission.EditUser))
        self.assertFalse(User.current_user_has_permissions_one_of(Permission.EditGlobalSettings, Permission.EditUser))

    def test_get_role_of_current_user_no_role(self):
        """
            Test the `get_role_of_current_user` method if the user does not have a role.

            Expected result: `None`
        """

        self.assertFalse(hasattr(current_user, 'role'))
        self.assertIsNone(User.get_role_of_current_user())

    def test_get_role_of_current_user_success(self):
        """
            Test the `get_role_of_current_user` method if the user has a role.

            Expected result: The role of the user is returned.
        """

        role = Role('Administrator')
        db.session.add(role)

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = role

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        self.assertEqual(role, User.get_role_of_current_user())

    # endregion

    # region DB Queries

    def test_get_search_query_no_term(self):
        """
            Test getting a search query without providing a search term.

            :return: A query is returned that does not filter.
        """

        user_1 = User('jane@example.com', 'Jane Doe')
        user_2 = User('john@example.com', 'John Doe')
        user_3 = User('max@beispiel.de', 'Max Mustermann')
        user_4 = User('erika@beispiel.de', 'Erika Musterfrau')
        db.session.add(user_1)
        db.session.add(user_2)
        db.session.add(user_3)
        db.session.add(user_4)
        db.session.commit()

        result = [
            user_1,
            user_2,
            user_3,
            user_4,
        ]

        query = User.get_search_query()
        self.assertIsNotNone(query)

        users = query.all()
        self.assertListEqual(result, users)

    def test_get_search_query_with_term_no_wildcards(self):
        """
            Test getting a search query providing a search term without wildcards.

            :return: A query is returned that filters exactly by the search term.
        """

        user_1 = User('jane@example.com', 'Jane Doe')
        user_2 = User('john@example.com', 'John Doe')
        user_3 = User('max@beispiel.de', 'Max Mustermann')
        user_4 = User('erika@beispiel.de', 'Erika Musterfrau')
        db.session.add(user_1)
        db.session.add(user_2)
        db.session.add(user_3)
        db.session.add(user_4)
        db.session.commit()

        # Matching term - name.
        query = User.get_search_query(search_term='Jane Doe')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1], users)

        # Matching term - email.
        query = User.get_search_query(search_term='erika@beispiel.de')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_4], users)

        # Not-matching term.
        query = User.get_search_query(search_term='Jennifer D\'oh')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([], users)

        # Partially matching term, but no wildcards, thus no result.
        query = User.get_search_query(search_term='J')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([], users)

    def test_get_search_query_with_term_wildcards(self):
        """
            Test getting a search query providing a search term without wildcards.

            :return: A query is returned that filters by the search term allowing for partial matches.
        """

        user_1 = User('jane@example.com', 'Jane Doe')
        user_2 = User('john@example.com', 'John Doe')
        user_3 = User('max@beispiel.de', 'Max Mustermann')
        user_4 = User('erika@beispiel.de', 'Erika Musterfrau')
        db.session.add(user_1)
        db.session.add(user_2)
        db.session.add(user_3)
        db.session.add(user_4)
        db.session.commit()

        # Matching term - name.
        query = User.get_search_query(search_term='*Muster*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_3, user_4], users)

        # Matching term - email.
        query = User.get_search_query(search_term='*example*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1, user_2], users)

        # Partially matching term with wildcard at the end.
        query = User.get_search_query(search_term='jane*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1], users)

        # Partially matching term with wildcard at the front.
        query = User.get_search_query(search_term='*Doe')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1, user_2], users)

        # Partially matching term with wildcard in the middle.
        query = User.get_search_query(search_term='J*e')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1, user_2], users)

        # Partially matching term with wildcard at the front and end, case-insensitive.
        query = User.get_search_query(search_term='*U*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_3, user_4], users)

        # Wildcard term matching everything.
        query = User.get_search_query(search_term='*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1, user_2, user_3, user_4], users)

        # Wildcard term matching nothing.
        query = User.get_search_query(search_term='A*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([], users)

    def test_get_search_query_with_base_query_and_term(self):
        """
            Test getting a search query providing a base query and a search term.

            :return: A query is returned that filters exactly by the search term.
        """

        user_1 = User('jane@example.com', 'Jane Doe')
        user_2 = User('john@example.com', 'John Doe')
        user_3 = User('max@beispiel.de', 'Max Mustermann')
        user_4 = User('erika@beispiel.de', 'Erika Musterfrau')
        db.session.add(user_1)
        db.session.add(user_2)
        db.session.add(user_3)
        db.session.add(user_4)
        db.session.commit()

        base_query = User.query.order_by(User.name.desc())

        # Matching term.
        query = User.get_search_query(query=base_query, search_term='J*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_2, user_1], users)

        # Test that a different result is returned without the given base query.
        query = User.get_search_query(search_term='J*')
        self.assertIsNotNone(query)
        users = query.all()
        self.assertListEqual([user_1, user_2], users)

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


class UserPaginationTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """

        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context('/')
        self.request_context.push()
        db.create_all()

        # Add a few test models.
        user_1 = User('a@example.com', 'A')
        user_2 = User('b@example.com', 'B')
        user_3 = User('c@example.com', 'C')
        user_4 = User('d@example.com', 'D')
        user_5 = User('e@example.com', 'E')
        user_6 = User('f@example.com', 'F')
        user_7 = User('g@example.com', 'G')
        db.session.add(user_1)
        db.session.add(user_2)
        db.session.add(user_3)
        db.session.add(user_4)
        db.session.add(user_5)
        db.session.add(user_6)
        db.session.add(user_7)
        db.session.commit()

    def tearDown(self):
        """
            Reset the test cases.
        """

        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def test_get_info_text_search_term_multiple(self):
        """
            Test getting the info text with a search term for multiple rows on a page.

            Expected result: The search term is included, the first and last row on the page are given.
        """

        self.request_context.request.args = {'page': 1}
        search_term = 'Aerarium'
        pagination = UserPagination(User.query)

        text = pagination.get_info_text(search_term)
        self.assertIn(f'users {pagination.first_row} to {pagination.last_row} of {pagination.total_rows}', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_search_term_single(self):
        """
            Test getting the info text with a search term for a single row on a page.

            Expected result: The search term is included, the first row on the page is given.
        """

        self.request_context.request.args = {'page': 3}
        search_term = 'Aerarium'
        pagination = UserPagination(User.query)

        text = pagination.get_info_text(search_term)
        self.assertIn(f'user {pagination.first_row} of {pagination.total_rows}', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_search_term_no_rows(self):
        """
            Test getting the info text with a search term for no rows on the page.

            Expected result: The search term is included, the info that no rows were found is given.
        """

        # Filter by some dummy value not related to the search term.
        self.request_context.request.args = {'page': 1}
        search_term = 'Aerarium'
        pagination = UserPagination(User.query.filter(User.id > 42))

        text = pagination.get_info_text(search_term)
        self.assertIn('No users', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_no_search_term_multiple(self):
        """
            Test getting the info text without a search term for multiple rows on a page.

            Expected result: The search term is not included, the first and last row on the page are given.
        """

        self.request_context.request.args = {'page': 1}
        pagination = UserPagination(User.query)

        text = pagination.get_info_text()
        self.assertIn(f'users {pagination.first_row} to {pagination.last_row} of {pagination.total_rows}', text)
        self.assertNotIn('matching “', text)

    def test_get_info_text_no_search_term_single(self):
        """
            Test getting the info text without a search term for a single row on a page.

            Expected result: The search term is not included, the first row on the page is given.
        """

        self.request_context.request.args = {'page': 3}
        pagination = UserPagination(User.query)

        text = pagination.get_info_text()
        self.assertIn(f'user {pagination.first_row} of {pagination.total_rows}', text)
        self.assertNotIn('matching “', text)

    def test_get_info_text_no_search_term_no_rows(self):
        """
            Test getting the info text without a search term for no rows on the page.

            Expected result: The search term is not included, the info that no rows were found is given.
        """

        # Filter the results to achieve zero rows.
        self.request_context.request.args = {'page': 1}
        pagination = UserPagination(User.query.filter(User.id > 42))

        text = pagination.get_info_text()
        self.assertIn('No users', text)
        self.assertNotIn('matching “', text)
