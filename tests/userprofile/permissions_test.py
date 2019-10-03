# -*- coding: utf-8 -*-

from unittest import TestCase

from app.userprofile import Permission
from app.userprofile.permissions import PermissionBase


class PermissionBaseTest(TestCase):

    def test_new_invalid_definition_duplicate_value(self):
        """
            Test defining new permissions with duplicate values.

            Expected Result: A value error is raised.
        """

        user_value = 4
        user_title = 'Edit users'
        user_description = 'Ability to edit all users'
        user_representation = f'<TestPermission.EditUser: {user_value}>'
        role_value = user_value
        role_title = 'Edit roles'
        role_description = 'Ability to edit all roles'
        role_representation = f'<TestPermission.EditRole: {role_value}>'

        # Defining permissions with duplicate values will raise a value error.
        with self.assertRaises(ValueError) as value_exception_cm:

            class TestPermission(PermissionBase):
                """
                    A permission enumeration for testing.
                """

                EditUser = (user_value, user_title, user_description)

                EditRole = (role_value, role_title, role_description)

            # Just a simple assignment so that the class is used.
            _ = TestPermission.EditUser

        error = f'Duplicate permission value found: {role_representation} -> {user_representation}'
        self.assertEqual(error, str(value_exception_cm.exception))

    def test_new_invalid_definition_not_a_power_of_two(self):
        """
            Test defining new permissions with values that are not a number of 2.

            Expected Result: A value error is raised.
        """

        user_value = 3
        user_title = 'Edit users'
        user_description = 'Ability to edit all users'

        # Defining permissions with values that are not a power of 2 will raise a value error.
        with self.assertRaises(ValueError) as value_exception_cm:

            class TestPermission(PermissionBase):
                """
                    A permission enumeration for testing.
                """

                EditUser = (user_value, user_title, user_description)

            # Just a simple assignment so that the class is used.
            _ = TestPermission.EditUser

        self.assertEqual('Permission values must be a power of 2', str(value_exception_cm.exception))

    def test_new_valid_definition(self):
        """
            Test defining new permissions with valid values.

            Expected Result: The permissions are correctly initialized.
        """

        user_value = 1
        user_title = 'Edit users'
        user_description = 'Ability to edit all users'
        role_value = 4

        class TestPermission(PermissionBase):
            """
                A permission enumeration for testing.
            """

            EditUser = (user_value, user_title, user_description)

            # The title and description are optional. The title will be set to the permission's name.
            EditRole = role_value

        self.assertEqual(user_value, TestPermission.EditUser.value)
        self.assertEqual(user_title, TestPermission.EditUser.title)
        self.assertEqual(user_description, TestPermission.EditUser.description)
        self.assertEqual(role_value, TestPermission.EditRole.value)
        self.assertEqual('EditRole', TestPermission.EditRole.title)
        self.assertIsNone(TestPermission.EditRole.description)


class PermissionTest(TestCase):

    def test_values_are_constant(self):
        """
            Test that the values of the permission members stay constant when editing the permission enumeration.

            Expected result: The values are as defined.
        """

        self.assertEqual(1, Permission.EditRole.value)
        self.assertEqual(2, Permission.EditUser.value)
        self.assertEqual(4, Permission.EditGlobalSettings.value)

    def test_display_texts(self):
        """
            Test that the display attributes `title` and `description` are set for all permissions.

            Expected result: The actual texts don't matter, but some texts must have been set for all permissions.
                             The title must not be the name, the description must not be `None`.
        """

        # noinspection PyTypeChecker
        for permission in list(Permission):
            self.assertNotEqual(permission.name, permission.title, msg=f'Permission {permission.name}')
            self.assertIsNotNone(permission.description, msg=f'Permission {permission.name}')
