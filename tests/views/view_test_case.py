# -*- coding: utf-8 -*-

from typing import Any
from typing import Dict
from typing import Optional

from unittest import TestCase

from flask import abort
from werkzeug.exceptions import NotFound

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User


class ViewTestCase(TestCase):

    # region Test Setup

    def setUp(self) -> None:
        """
            Prepare the test cases.
        """

        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

    def tearDown(self) -> None:
        """
            Clean up after each test case.
        """

        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    # endregion

    # region Helper Methods

    def get(self, url: str, expected_status: int = 200, follow_redirects: bool = True) -> str:
        """
            Access the given URL via HTTP GET. Assert that the returned status code is the given one.

            The status code is checked using `self.assertEqual`.

            :param url: The URL to access.
            :param expected_status: The status code that should be returned. Defaults to `200`.
            :param follow_redirects: Set to `False` if redirects by the route should not be followed. Defaults to
                                     `True`.
            :return: The response of accessing the URL as a string.
        """

        response = self.client.get(url, follow_redirects=follow_redirects)
        data = response.get_data(as_text=True)

        self.assertEqual(expected_status, response.status_code, msg='Expected Status Code')

        return data

    def post(self, url: str, data: Dict[str, Any] = None, expected_status: int = 200, follow_redirects: bool = True)\
            -> str:
        """
            Access the given URL via HTTP POST, sending the given data. Assert that the returned status code is the
            given one.

            The status code is checked using `self.assertEqual`.

            :param url: The URL to access.
            :param data: The data to send in the POST request. Defaults to `dict()`.
            :param expected_status: The status code that should be returned. Defaults to `200`.
            :param follow_redirects: Set to `False` if redirects by the route should not be followed. Defaults to
                                     `True`.
            :return: The response of accessing the URL as a string.
        """

        if data is None:
            data = dict()

        response = self.client.post(url, follow_redirects=follow_redirects, data=data)
        data = response.get_data(as_text=True)

        self.assertEqual(expected_status, response.status_code, msg='Expected Status Code')

        return data

    @staticmethod
    def create_user(email: str, name: str, password: str, role: Optional[Role] = None) -> User:
        """
            Create a user with the given parameters. If a role is given, assign the role to the user. Commit this user
            to the DB.

            :param email: The email address of the user.
            :param name: The name of the user.
            :param password: The password of the user.
            :param role: The role for the user. Defaults to `None`.
            :return: The created user.
        """

        user = User(email, name)
        user.set_password(password)

        if role:
            user.role = role

        db.session.add(user)
        db.session.commit()

        return user

    def create_and_login_user(self,
                              email: str = 'doe@example.com',
                              name: str = 'Jane Doe',
                              password: str = 'ABC123!',
                              role: Optional[Role] = None
                              ) -> User:
        """
            Create a user with the given parameters and log them in. If a role is given, assign the role to the user.
            The user is committed to the DB.

            :param email: The email address of the user. Defaults to `'doe@example.com'`.
            :param name: The name of the user. Defaults to `'Jane Doe'`.
            :param password: The password of the user. Defaults to `'ABC123!'`.
            :param role: The role for the user. Defaults to `None`.
            :return: The created user.
        """

        user = self.create_user(email, name, password, role)
        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password,
        ))

        return user

    @staticmethod
    def create_role(*permissions: Permission, name: str = 'Test Role') -> Role:
        """
            Create a role with the given permissions.

            :param permissions: The permissions of the role.
            :param name: The name of the new role. Defaults to `'Test Role'`.
            :return: The created role.
        """

        role = Role(name)
        for permission in permissions:
            role.permissions |= permission

        db.session.add(role)
        db.session.commit()

        return role

    @staticmethod
    def aborting_route(code: int) -> None:
        """
            A route handler that aborts with the given status code.

            :param code: The status code of the HTTP response.
        """

        abort(code)

    @classmethod
    def get_false(cls) -> bool:
        """
            Get `False`. Useful for mocking.

            This method must be a class method so that it can be used in the patch decorator when mocking another
            method.

            :return: `False`
        """

        return False

    # endregion

    # region Tests

    def test_get_with_correct_status(self) -> None:
        """
            Test accessing a URL via HTTP GET and expecting the correct status.

            Expected result: The response data is returned. No error is raised.
        """

        self.create_and_login_user()

        data = self.get('/user/login')
        self.assertIn('Logout', data)

    def test_get_with_incorrect_status(self) -> None:
        """
            Test accessing a URL via HTTP GET and expecting an incorrect status.

            Expected result: The response data is returned. No error is raised.
        """

        self.create_and_login_user()

        with self.assertRaises(self.failureException):
            self.get('/user/login', expected_status=404)

    def test_post_with_correct_status(self) -> None:
        """
            Test accessing a URL via HTTP POST and expecting the correct status.

            Expected result: The response data is returned. No error is raised.
        """

        email = 'jane@doe.com'
        name = 'Jane Doe'
        password = 'ABC123!'
        self.create_user(email, name, password)

        data = self.post('/user/login', data=dict(
            email=email,
            password=password,
        ))
        self.assertIn('Welcome', data)
        self.assertNotIn('Log In', data)

    def test_post_with_incorrect_status(self) -> None:
        """
            Test accessing a URL via HTTP POST and expecting an incorrect status.

            Expected result: The response data is returned. No error is raised.
        """

        email = 'jane@doe.com'
        name = 'Jane Doe'
        password = 'ABC123!'
        self.create_user(email, name, password)

        with self.assertRaises(self.failureException):
            self.post('/user/login', expected_status=404, data=dict(
                email=email,
                password=password,
            ))

    def test_create_user_without_role(self) -> None:
        """
            Test creating a new user without a role.

            Expected result: The user is created with the given parameters and without a role. The user is saved on the
                             DB.
        """

        email = 'john@doe.com'
        name = 'John Doe'
        password = '123ABC$'
        user = self.create_user(email, name, password)

        self.assertIsNotNone(user)
        self.assertEqual(email, user.email)
        self.assertEqual(name, user.name)
        self.assertTrue(user.check_password(password))
        self.assertIsNone(user.role)
        self.assertEqual(user, User.load_from_id(user.id))

    def test_create_user_with_role(self) -> None:
        """
            Test creating a new user with a given role.

            Expected result: The user is created with the given parameters and the role. The user is saved on the DB.
        """

        role = self.create_role(Permission.EditUser, Permission.EditRole)

        email = 'john@doe.com'
        name = 'John Doe'
        password = '123ABC$'
        user = self.create_user(email, name, password, role)

        self.assertIsNotNone(user)
        self.assertEqual(email, user.email)
        self.assertEqual(name, user.name)
        self.assertTrue(user.check_password(password))
        self.assertEqual(role, user.role)
        self.assertEqual(user, User.load_from_id(user.id))

    def test_create_and_login_user(self) -> None:
        """
            Test creating a new user and logging them in.

            Expected result: The user is created and logged in.
        """

        user = self.create_and_login_user()

        self.assertIsNotNone(user)
        self.assertEqual('doe@example.com', user.email)
        self.assertEqual('Jane Doe', user.name)
        self.assertTrue(user.check_password('ABC123!'))
        self.assertIsNone(user.role)
        self.assertEqual(user, User.load_from_id(user.id))

        # Check if the login was successful by checking if the login page is shown.
        response = self.client.get('/user/login', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertNotIn('<h1>Log In</h1>', data)
        self.assertIn('<h1>Dashboard</h1>', data)

    def test_create_role(self) -> None:
        """
            Test creating a new role.

            Expected result: The role is created with the given permissions.
        """

        name = 'Administrator'
        role = self.create_role(Permission.EditUser, Permission.EditRole, name=name)

        self.assertIsNotNone(role)
        self.assertEqual(name, role.name)
        self.assertTrue(role.has_permissions_all(Permission.EditUser, Permission.EditRole))
        self.assertFalse(role.has_permissions_one_of(Permission.EditGlobalSettings))
        self.assertEqual(role, Role.load_from_id(role.id))

    def test_aborting_route(self) -> None:
        """
            Test the aborting route handler for a 404 error.

            :return: The NotFound error is raised.
        """

        with self.assertRaises(NotFound):
            self.aborting_route(404)

    def test_get_false(self) -> None:
        """
            Test getting `False`.

            Expected Result: `False`.
        """

        self.assertFalse(self.get_false())

    # endregion
