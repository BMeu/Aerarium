# -*- coding: utf-8 -*-

from typing import Any
from typing import Dict
from typing import Optional
from typing import Set

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

    def check_allowed_methods(self, url: str, allowed_methods: Optional[Set[str]] = None, allow_options: bool = True)\
            -> None:
        """
            Check if the given URL can be accessed only by the specified methods.

            This method will assert that the URL can be accessed by all HTTP methods listed in `allowed_methods` by
            checking that a request via each of these methods to the URL does not return a response code of 405.
            Likewise, it will test that all methods not listed in `allowed_methods` return a response code of 405.

            Flask by default allows 'OPTIONS'. This method follows this behaviour and automatically adds 'OPTIONS' to
            the set of allowed methods unless configured otherwise.

            Flask also automatically allows 'HEAD' if 'GET' is allowed. This method follows this behaviour and always
            adds 'HEAD' to the set of allowed methods if 'GET' is included in the set.

            :param url: The URL to check.
            :param allowed_methods: A set of all HTTP methods via which the URL can be accessed. If the set is not given
                                    or an empty set of allowed methods is passed, 'GET' will automatically be allowed
                                    to mimic Flask's behaviour. Defaults to `None`.
            :param allow_options: If this parameter is set to `True`, 'OPTIONS' will automatically be added to the set
                                  of allowed methods to follow Flask's behaviour. Defaults to `True`.
        """

        all_methods = ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT']

        # Be default, 'GET' is the only allowed method.
        if allowed_methods is None or not allowed_methods:
            allowed_methods = {'GET'}

        # If 'GET' is allowed, Flask also allows 'HEAD' automatically.
        if 'GET' in allowed_methods:
            allowed_methods.add('HEAD')

        # Follow Flask's behaviour and add 'OPTIONS' by default.
        if allow_options:
            allowed_methods.add('OPTIONS')

        prohibited_methods = [method for method in all_methods if method not in allowed_methods]

        for allowed_method in allowed_methods:
            status_code = self._get_status_code_for_method(url, allowed_method)
            self.assertNotEqual(405, status_code, f'{allowed_method} {url} is not allowed, but should be.')

        for prohibited_method in prohibited_methods:
            status_code = self._get_status_code_for_method(url, prohibited_method)
            self.assertEqual(405, status_code, f'{prohibited_method} {url} is allowed, but should not be.')

    def _get_status_code_for_method(self, url: str, method: str) -> int:
        """
            Access the given URL via the given HTTP method and return the response status code.

            :param url: The URL to access.
            :param method: The HTTP method used to access the URL.
            :return: The HTTP status code that accessing the URL via the method returned.
            :raise ValueError: if the HTTP method is invalid.
        """

        if method == 'DELETE':
            response = self.client.delete(url)
        elif method == 'GET':
            response = self.client.get(url)
        elif method == 'HEAD':
            response = self.client.head(url)
        elif method == 'OPTIONS':
            response = self.client.options(url)
        elif method == 'PATCH':
            response = self.client.patch(url)
        elif method == 'POST':
            response = self.client.post(url)
        elif method == 'PUT':
            response = self.client.put(url)
        else:
            raise ValueError(f'Invalid HTTP method {method}')

        return response.status_code

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

    @staticmethod
    def example_route() -> str:
        """
            A route handler that returns an example string as its response.

            :return: 'Hello, world!'
        """

        return 'Hello, world!'

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

    def test_post_with_correct_status_and_no_data(self) -> None:
        """
            Test accessing a URL via HTTP POST and expecting the correct status, but passing no data.

            Expected result: The response data is returned. No error is raised.
        """

        email = 'jane@doe.com'
        name = 'Jane Doe'
        password = 'ABC123!'
        self.create_user(email, name, password)

        data = self.post('/user/login')
        self.assertNotIn('Welcome', data)
        self.assertIn('Log In', data)

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

    def test_check_allowed_methods_without_assertion_failures(self) -> None:
        """
            Test checking the allowed and prohibited methods of a URL when all assertions hold.

            Expected result: No error is raised. 'OPTIONS' and 'HEAD' are automatically added to the allowed methods.
        """

        allowed_methods = ['GET', 'POST', 'PUT', 'OPTIONS', 'HEAD']
        self.app.add_url_rule('/example', 'example', self.example_route, methods=allowed_methods)

        self.check_allowed_methods('/example', {'GET', 'POST', 'PUT'})

    def test_check_allowed_methods_with_unexpectedly_allowed_method(self) -> None:
        """
            Test checking the allowed and prohibited methods of a URL when there is a method that is allowed but
            shouldn't be.

            Expected result: An assertion error is raised with a message describing the failure.
        """

        self.app.add_url_rule('/example', 'example', self.example_route, methods=['POST', 'PUT'])

        # PUT is allowed, but should not be allowed.
        with self.assertRaises(self.failureException) as exception_cm:
            self.check_allowed_methods('/example', {'POST'})

        self.assertEqual('PUT /example is allowed, but should not be.', exception_cm.exception.msg)

    def test_check_allowed_methods_with_unexpectedly_prohibited_method(self) -> None:
        """
            Test checking the allowed and prohibited methods of a URL when there is a method that is prohibited but
            shouldn't be.

            Expected result: An assertion error is raised with a message describing the failure.
        """

        self.app.add_url_rule('/example', 'example', self.example_route, methods=['POST'])

        # PUT is not allowed, but should be.
        with self.assertRaises(self.failureException) as exception_cm:
            self.check_allowed_methods('/example', {'POST', 'PUT'})

        # The error object does not have a `msg` attribute if it is raised from `assertNotEqual`.
        self.assertEqual('405 == 405 : PUT /example is not allowed, but should be.', str(exception_cm.exception))

    def test_check_allowed_methods_with_default_methods(self) -> None:
        """
            Test checking the allowed and prohibited methods of a URL when not specifying the allowed methods.

            Expected result: 'GET' is automatically allowed and thus, will not raise an error.
        """

        self.app.add_url_rule('/example', 'example', self.example_route, methods=['GET'])

        self.check_allowed_methods('/example')

    def test_check_allowed_methods_without_options(self) -> None:
        """
            Test checking the allowed and prohibited methods of a URL when not automatically adding 'OPTIONS' to the
            allowed methods.

            Expected result: An error is raised that 'OPTIONS' is allowed, but should not be.
        """

        self.app.add_url_rule('/example', 'example', self.example_route, methods=['GET', 'OPTIONS'])

        with self.assertRaises(self.failureException) as exception_cm:
            self.check_allowed_methods('/example', {'GET'}, allow_options=False)

        self.assertEqual('OPTIONS /example is allowed, but should not be.', exception_cm.exception.msg)

    def test_get_status_code_for_method_delete(self) -> None:
        """
            Test that accessing a URL via DELETE.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/delete', 'delete', self.example_route, methods=['DELETE'])

        status_code = self._get_status_code_for_method('/delete', 'DELETE')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_get(self) -> None:
        """
            Test that accessing a URL via GET.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/get', 'get', self.example_route, methods=['GET'])

        status_code = self._get_status_code_for_method('/get', 'GET')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_head(self) -> None:
        """
            Test that accessing a URL via HEAD.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/head', 'head', self.example_route, methods=['HEAD'])

        status_code = self._get_status_code_for_method('/head', 'HEAD')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_options(self) -> None:
        """
            Test that accessing a URL via OPTIONS.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/options', 'options', self.example_route, methods=['OPTIONS'])

        status_code = self._get_status_code_for_method('/options', 'OPTIONS')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_patch(self) -> None:
        """
            Test that accessing a URL via PATCH.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/patch', 'patch', self.example_route, methods=['PATCH'])

        status_code = self._get_status_code_for_method('/patch', 'PATCH')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_post(self) -> None:
        """
            Test that accessing a URL via POST.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/post', 'post', self.example_route, methods=['POST'])

        status_code = self._get_status_code_for_method('/post', 'POST')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_put(self) -> None:
        """
            Test that accessing a URL via PUT.

            Expected result: The correct status code is returned.
        """

        self.app.add_url_rule('/put', 'put', self.example_route, methods=['PUT'])

        status_code = self._get_status_code_for_method('/put', 'PUT')
        self.assertEqual(200, status_code)

    def test_get_status_code_for_method_invalid_method(self) -> None:
        """
            Test that accessing a URL via an invalid method.

            Expected result: A value error is raised.
        """

        with self.assertRaises(ValueError) as exception_cm:
            self._get_status_code_for_method('/invalid', 'INVALID')

        self.assertEqual('Invalid HTTP method INVALID', str(exception_cm.exception))

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

            Expected result: The NotFound error is raised.
        """

        with self.assertRaises(NotFound):
            self.aborting_route(404)

    def test_example_route(self) -> None:
        """
            Test the example route handle.

            Expected result: 'Hello, world!' is returned.
        """

        self.assertEqual('Hello, world!', self.example_route())

    def test_get_false(self) -> None:
        """
            Test getting `False`.

            Expected Result: `False`.
        """

        self.assertFalse(self.get_false())

    # endregion
