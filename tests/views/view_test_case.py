# -*- coding: utf-8 -*-

from typing import Any
from typing import Dict
from typing import Optional
from typing import Set

from unittest import TestCase

from flask import abort

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User


class ViewTestCase(TestCase):
    """
        This class is a base test case for all view tests, providing helpful methods that are needed in many situations
        when testing views.
    """

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

    # region Route Accessing

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

    def post(self, url: str, data: Dict[str, Any] = None, expected_status: int = 200, follow_redirects: bool = True) \
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

    # TODO: Rename assert_allowed_methods().
    def check_allowed_methods(self, url: str, allowed_methods: Optional[Set[str]] = None, allow_options: bool = True) \
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

    # endregion

    # region Permissions

    def assert_no_permission_required(self, url: str, method: str = 'GET') -> None:
        """
            Assert that accessing the URL via the given method requires no permission at all and that accessing the URL
            with any permission is actually possible.

            The test checks for a response code of 403. This can lead to a false positive if a route aborts with an
            error 403.

            :param url: The URL to access.
            :param method: The HTTP method to access the URL by. Defaults to `'GET'`.
        """

        allowed_permissions = Permission.get_permissions(include_empty_permission=True, all_combinations=True)
        self._assert_permissions(url, allowed_permissions, method)

    def assert_permission_required(self, url: str, permission: Permission, method: str = 'GET') -> None:
        """
            Assert that accessing the URL via the given method requires the specified permission and that accessing the
            URL with the permission is actually possible.

            The test checks for a response code of 403. This can lead to a false positive if a route does not require
            the specified permission but aborts with an error 403 in some other case.

            :param url: The URL to access.
            :param permission: The permission that must be required to access the URL.
            :param method: The HTTP method to access the URL by. Defaults to `'GET'`.
        """

        all_permissions = Permission.get_permissions(include_empty_permission=True, all_combinations=True)
        allowed_permissions = {p for p in all_permissions if p.includes_permission(permission)}

        self._assert_permissions(url, allowed_permissions, method)

    def assert_permission_required_one_of(self, url: str, *permissions: Permission, method: str = 'GET') -> None:
        """
            Assert that accessing the URL via the given method requires one of the specified permissions and that
            accessing the URL with the permission is actually possible, while accessing the URL with any other
            permission fails.

            :param url: The url to access.
            :param permissions: The permissions that must be required to access the URL.
            :param method: The HTTP method to access the URL by. Defaults to `'GET'`.
        """

        all_permissions = Permission.get_permissions(include_empty_permission=True, all_combinations=True)
        allowed_permissions = set({})
        for permission in permissions:
            allowed_permissions.update({p for p in all_permissions if p.includes_permission(permission)})

        self._assert_permissions(url, allowed_permissions, method)

    def assert_permission_required_all(self, url: str, *permissions: Permission, method: str = 'GET') -> None:
        """
            Assert that accessing the URL via the given method requires all of the specified permissions and that
            accessing the URL with the permissions is actually possible.

            :param url: The URL to access.
            :param permissions: The permissions that must be required to access the URL.
            :param method: The HTTP method to access the URL by. Defaults to `'GET'`.
        """

        all_permissions = Permission.get_permissions(include_empty_permission=True, all_combinations=True)

        #
        allowed_permission = Permission(0)
        for permission in permissions:
            allowed_permission |= permission

        allowed_permissions = {p for p in all_permissions if p.includes_permission(allowed_permission)}

        self._assert_permissions(url, allowed_permissions, method)

    def _assert_permission_grants_access(self, url: str, permission: Permission, method: str = 'GET') -> None:
        """
            Assert that the given permission is sufficient to access the given URL.

            :param url: The URL to access.
            :param permission: The permission that should be able to able to access the URL.
            :param method: The HTTP method to access the URL by. Defaults to `'GET'`.
        """

        # Create and log in a user with the given permission.
        role = self.create_role(permission)
        user = self.create_and_login_user(role=role)

        # Ensure that accessing the URL with the given permission is possible.
        status_code = self._get_status_code_for_method(url, method)
        self.assertNotEqual(403, status_code,
                            f'{method} {url} must be accessible with permission {permission}, but it is not.')

        # Delete the user and role so that this method can be called multiple times in the same test.
        # Since the role might be the only role with permissions to edit roles, we cannot use role.delete() which will
        # fail in such a case.
        user._delete()
        db.session.delete(role)
        db.session.commit()

    def _assert_permission_does_not_grant_access(self, url: str, permission: Permission, method: str = 'GET') -> None:
        """
            Assert that the given permission is not sufficient to access the given URL.

            :param url: The URL to access.
            :param permission: The permission that should not be able to able to access the URL.
            :param method: The HTTP method to access the URL by. Defaults to `'GET'`.
        """

        # Create and log in a user with the given permission.
        role = self.create_role(permission)
        user = self.create_and_login_user(role=role)

        # Ensure that accessing the URL with the given permission is impossible.
        status_code = self._get_status_code_for_method(url, method)
        self.assertEqual(403, status_code,
                         f'{method} {url} must not be accessible with permission {permission}, but it is.')

        # Delete the user and role so that this method can be called multiple times in the same test.
        # Since the role might be the only role with permissions to edit roles, we cannot use role.delete() which will
        # fail in such a case.
        user._delete()
        db.session.delete(role)
        db.session.commit()

    def _assert_permissions(self, url: str, allowed_permissions: Set[Permission], method: str) -> None:
        """
            Assert that the given URL can be accessed with the allowed permissions, but not with any other permission.

            :param url: The URL to access.
            :param allowed_permissions: List of permissions that must be able to access the URL.
            :param method: The HTTP method to access the URL by.
        """

        for allowed_permission in allowed_permissions:
            self._assert_permission_grants_access(url, allowed_permission, method)

        all_permissions = Permission.get_permissions(include_empty_permission=True, all_combinations=True)
        prohibited_permissions = {permission for permission in all_permissions if permission not in allowed_permissions}
        for prohibited_permission in prohibited_permissions:
            self._assert_permission_does_not_grant_access(url, prohibited_permission, method)

    # endregion

    # region Application Entities

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

    # endregion

    # region Routes

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

    # endregion

    # region Other Helper Methods

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
