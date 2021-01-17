# -*- coding: utf-8 -*-

from unittest import TestCase

from flask import url_for
from flask_login import current_user
from flask_login import login_user
from werkzeug.exceptions import Forbidden
from werkzeug.wrappers import Response

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import logout_required
from app.userprofile import Permission
from app.userprofile import permission_required
from app.userprofile import permission_required_all
from app.userprofile import permission_required_one_of
from app.userprofile import Role
from app.userprofile import User


class DecoratorsTest(TestCase):

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

    @staticmethod
    def view_function() -> str:
        """
            A simple test "view" function.

            :return: 'Decorated View'.
        """

        return 'Decorated View'

    def test_logout_required_logged_out(self):
        """
            Test the `logout_required` decorator with an anonymous user.

            Expected result: The decorated view function is returned.
        """

        view_function = logout_required(self.view_function)
        response = view_function()
        self.assertEqual(self.view_function(), response)

    def test_logout_required_logged_in(self):
        """
            Test the `logout_required` decorator with a logged-in user.

            Expected result: The redirect response to the home page is returned.
        """

        email = 'test@example.com'
        name = 'John Doe'
        user = User(email, name)

        db.session.add(user)
        db.session.commit()
        login_user(user)

        redirect_function = logout_required(self.view_function)
        response = redirect_function()
        self.assertIsInstance(response, Response)
        self.assertEqual(302, response.status_code)
        self.assertEqual(url_for('main.index'), response.location)

    def test_permission_required_no_role(self):
        """
            Test the `permission_required` decorator if the user does not have a role.

            Expected result: The request is aborted with an error 403.
        """

        # Ensure the user has no role.
        self.assertFalse(hasattr(current_user, 'role'))

        with self.assertRaises(Forbidden):
            permission_required(Permission.EditRole)(self.view_function)()

    def test_permission_required_no_permission(self):
        """
            Test the `permission_required` decorator if the user does not have the requested permission.

            Expected result: The request is aborted with an error 403.
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
        self.assertFalse(user.role.has_permission(permission))

        with self.assertRaises(Forbidden):
            permission_required(permission)(self.view_function)()

    def test_permission_required_has_permission(self):
        """
            Test the `permission_required` decorator if the user has the requested permission.

            Expected result: The decorated view function is returned.
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

        view_function = permission_required(permission)(self.view_function)
        response = view_function()
        self.assertEqual(self.view_function(), response)

    def test_permission_required_all_not_all_permissions(self):
        """
            Test the `permission_required_all` decorator if the user does not have all the requested permissions.

            Expected result: The request is aborted with an error 403.
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role('Administrator')
        user.role.permissions = Permission.EditRole

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        self.assertTrue(user.role.has_permission(Permission.EditRole))
        self.assertFalse(user.role.has_permission(Permission.EditUser))

        with self.assertRaises(Forbidden):
            permission_required_all(Permission.EditRole, Permission.EditUser)(self.view_function)()

    def test_permission_required_all_has_permissions(self):
        """
            Test the `permission_required` decorator if the user has all the requested permission.

            Expected result: The decorated view function is returned.
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role('Administrator')
        user.role.permissions = Permission.EditRole | Permission.EditUser

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        self.assertTrue(user.role.has_permissions_all(Permission.EditRole, Permission.EditUser))

        view_function = permission_required_all(Permission.EditRole, Permission.EditUser)(self.view_function)
        response = view_function()
        self.assertEqual(self.view_function(), response)

    def test_permission_required_one_of_no_permission(self):
        """
            Test the `permission_required_one_of` decorator if the user does not have any of the requested permissions.

            Expected result: The request is aborted with an error 403.
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

        self.assertEqual(Permission(0), user.role.permissions)

        with self.assertRaises(Forbidden):
            permission_required_one_of(Permission.EditRole, Permission.EditUser)(self.view_function)()

    def test_permission_required_one_of_has_permission(self):
        """
            Test the `permission_required` decorator if the user has one of the requested permission, but not all.

            Expected result: The decorated view function is returned.
        """

        email = 'test@example.com'
        name = 'Jane Doe'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = Role('Administrator')
        user.role.permissions = Permission.EditRole

        db.session.add(user)
        db.session.commit()

        user.login(email, password)

        self.assertTrue(user.role.has_permission(Permission.EditRole))
        self.assertFalse(user.role.has_permission(Permission.EditUser))

        view_function = permission_required_one_of(Permission.EditRole, Permission.EditUser)(self.view_function)
        response = view_function()
        self.assertEqual(self.view_function(), response)
