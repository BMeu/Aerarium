# -*- coding: utf-8 -*-

from typing import Set

from werkzeug.exceptions import NotFound

from app.userprofile import Permission
from app.userprofile import permission_required
from app.userprofile import permission_required_all
from app.userprofile import permission_required_one_of
from app.userprofile import Role
from app.userprofile import User
from tests.views import ViewTestCase


class ViewTestCaseTest(ViewTestCase):

    # region Route Accessing

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

        self.assertEqual('405 != 200 : PUT /example is allowed, but should not be.', str(exception_cm.exception))

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

        self.assertEqual('405 != 200 : OPTIONS /example is allowed, but should not be.', str(exception_cm.exception))

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

    # endregion

    # region Permissions

    @staticmethod
    def _get_messages_for_inaccessible_url(permissions: Set[Permission]) -> Set[str]:
        """
            Get the failure message for each given permission when a URL should be accessible with the permission,
            but it is not.

            The HTTP method in the message will always be 'GET', the URL '/example'.

            :param permissions: The permissions for which the failure messages will be created.
            :return: A set of all messages, one for each permission.
        """

        messages = set()
        for permission in permissions:
            messages.add(f'403 == 403 : GET /example must be accessible with permission {permission}, but it is not.')

        return messages

    @staticmethod
    def _get_messages_for_accessible_url(permissions: Set[Permission]) -> Set[str]:
        """
            Get the failure message for each given permission when a URL should not be accessible with the permission,
            but it is.

            The HTTP method in the message will always be 'GET', the URL '/example', the actual status code 200.

            :param permissions: The permissions for which the failure messages will be created.
            :return: A set of all message, one for each permissions.
        """

        messages = set()
        for permission in permissions:
            messages.add(f'403 != 200 : GET /example must not be accessible with permission {permission}, but it is.')

        return messages

    def test_assert_no_permission_required_if_no_permission_is_required(self) -> None:
        """
            Test the assertion `assert_no_permission_required` if the accessed URL does in fact not require any
            permissions.

            Expected result: No errors are raised.
        """

        self.app.add_url_rule('/example', 'example', self.example_route, methods=['GET', 'POST'])

        self.assert_no_permission_required('/example')
        self.assert_no_permission_required('/example', method='POST')

    def test_assert_no_permission_required_but_url_requires_a_permission(self) -> None:
        """
            Test the assertion `assert_no_permission_required` if the accessed URL requires a permission.

            Expected result: An error is raised for any permission other than the required one.
        """

        decorator = permission_required(Permission.EditUser)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_no_permission_required('/example')

        # The assertion can fail for any of these permissions since the assertion uses sets.
        expected_messages = self._get_messages_for_inaccessible_url({
            Permission(0),
            Permission.EditRole,
            Permission.EditGlobalSettings,
            Permission.EditRole | Permission.EditGlobalSettings
        })

        self.assertIn(str(exception_cm.exception), expected_messages)

    def test_assert_permission_required_with_correct_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required` with the permission that the accessed URL requires.

            Expected result: No errors are raised.
        """

        decorator = permission_required(Permission.EditRole)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view, methods=['GET', 'POST'])

        self.assert_permission_required('/example', Permission.EditRole)
        self.assert_permission_required('/example', Permission.EditRole, method='POST')

    def test_assert_permission_required_with_incorrect_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required` with a different permission than the one required by the
            URL.

            Expected result: An error is raised than the different one.
        """

        decorator = permission_required(Permission.EditRole)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_permission_required('/example', Permission.EditUser)

        # The assertion can fail for any of these permissions since the assertion uses sets.
        expected_messages = self._get_messages_for_inaccessible_url({
            Permission.EditUser,
            Permission.EditUser | Permission.EditGlobalSettings,
        })

        self.assertIn(str(exception_cm.exception), expected_messages)

    def test_assert_permission_required_without_required_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required` assuming that a URL requires a permission, while in fact, it
            does not.

            Expected result: An error is raised for any other permission than the assumed one.
        """

        self.app.add_url_rule('/example', 'example', self.example_route)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_permission_required('/example', Permission.EditUser)

        expected_messages = self._get_messages_for_accessible_url({
            Permission(0),
            Permission.EditRole,
            Permission.EditGlobalSettings,
            Permission.EditRole | Permission.EditGlobalSettings,
        })
        self.assertIn(str(exception_cm.exception), expected_messages)

    def test_assert_permission_required_one_of_with_correct_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required_one_of` with the same permissions that are required by the
            URL.

            Expected result: No errors are raised.
        """

        decorator = permission_required_one_of(Permission.EditRole, Permission.EditUser)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view, methods=['GET', 'POST'])

        self.assert_permission_required_one_of('/example', Permission.EditRole, Permission.EditUser)
        self.assert_permission_required_one_of('/example', Permission.EditRole, Permission.EditUser, method='POST')

    def test_assert_permission_required_one_of_with_too_many_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required_one_of` with more permissions than actually required by the
            URL.

            Expected result: An error is raised for the permission that is given in the assertion, but in in fact not
                             required.
        """

        decorator = permission_required_one_of(Permission.EditRole, Permission.EditUser)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_permission_required_one_of('/example', Permission.EditRole, Permission.EditUser,
                                                   Permission.EditGlobalSettings)

        expected_messages = self._get_messages_for_inaccessible_url({
            Permission.EditGlobalSettings,
        })
        self.assertIn(str(exception_cm.exception), expected_messages)

    def test_assert_permission_required_one_of_with_too_few_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required_one_of` with fewer permissions than actually required by the
            URL.

            Expected result: An error is raised for the permission that is in fact required, but not given in the
                             assertion.
        """

        decorator = permission_required_one_of(Permission.EditRole, Permission.EditUser, Permission.EditGlobalSettings)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_permission_required_one_of('/example', Permission.EditRole, Permission.EditUser)

        expected_messages = self._get_messages_for_accessible_url({
            Permission.EditGlobalSettings,
        })
        self.assertIn(str(exception_cm.exception), expected_messages)

    def test_assert_permission_required_all_with_correct_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required_all` with the same permissions that are required by the
            URL.

            Expected result: No errors are raised.
        """

        decorator = permission_required_all(Permission.EditRole, Permission.EditUser)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view, methods=['GET', 'POST'])

        self.assert_permission_required_all('/example', Permission.EditRole, Permission.EditUser)
        self.assert_permission_required_all('/example', Permission.EditRole, Permission.EditUser, method='POST')

    def test_assert_permission_required_all_with_too_many_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required_all` with more permissions than actually required by the URL.

            Expected result: An error is raised that the URL is accessible with the permissions that are actually
                             required.
        """

        decorator = permission_required_all(Permission.EditRole, Permission.EditUser)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_permission_required_all('/example', Permission.EditRole, Permission.EditUser,
                                                Permission.EditGlobalSettings)

        expected_messages = self._get_messages_for_accessible_url({
            Permission.EditUser | Permission.EditRole,
        })

        self.assertIn(str(exception_cm.exception), expected_messages)

    def test_assert_permission_required_all_with_too_few_permissions(self) -> None:
        """
            Test the assertion `assert_permission_required_all` with fewer permissions than actually required by the
            URL.

            Expected result: An error is raised that the URL is not accessible with the permissions given in the
                             assertion.
        """

        decorator = permission_required_all(Permission.EditRole, Permission.EditUser, Permission.EditGlobalSettings)
        decorated_view = decorator(self.example_route)
        self.app.add_url_rule('/example', 'example', decorated_view)

        with self.assertRaises(self.failureException) as exception_cm:
            self.assert_permission_required_all('/example', Permission.EditRole, Permission.EditUser)

        expected_messages = self._get_messages_for_inaccessible_url({
            Permission.EditUser | Permission.EditRole,
        })

        self.assertIn(str(exception_cm.exception), expected_messages)

    # endregion

    # region Application Entities

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

    # endregion

    # region Routes

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

    # endregion

    # region Other Helper Methods

    def test_get_false(self) -> None:
        """
            Test getting `False`.

            Expected Result: `False`.
        """

        self.assertFalse(self.get_false())

    # endregion
