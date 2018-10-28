#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from flask_login import current_user

from app import create_app
from app import db
from app.authorization import User
from app.configuration import TestConfiguration


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
        self.assertEqual(email, user.email)
        self.assertEqual(name, user.name)
        self.assertIsNone(user._is_activated)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(1, user.id)
        self.assertTrue(user._is_activated)

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

    def test_load_from_db_success(self):
        """
            Test the user loader function with an existing user.

            Expected result: The user with the given is returned.
        """
        email = 'test@example.com'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user_id, user.id)

        loaded_user = User.load_from_db(user_id)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user_id, loaded_user.id)
        self.assertEqual(email, loaded_user.email)
        self.assertEqual(name, loaded_user.name)

    def test_load_from_db_failure(self):
        """
            Test the user loader function with a non-existing user.

            Expected result: None is returned.
        """
        loaded_user = User.load_from_db(1)
        self.assertIsNone(loaded_user)
