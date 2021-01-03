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

    def test_get_permissions_without_empty_permission_and_combinations(self) -> None:
        """
            Test getting all permissions, without the empty permission and combinations.

            Expected result: All defined permissions are returned, without any extra elements in the result.
        """

        class TestPermission(PermissionBase):
            """
                A permission enumeration for testing.
            """

            EditUser = 1
            EditRole = 2
            EditGlobalSettings = 4

        expected_permissions = {
            TestPermission.EditUser,
            TestPermission.EditRole,
            TestPermission.EditGlobalSettings,
        }

        permissions = TestPermission.get_permissions()
        self.assertSetEqual(expected_permissions, permissions)

    def test_get_permissions_with_empty_permission_and_without_combinations(self) -> None:
        """
            Test getting all permissions, including the empty permission, but no combinations.

            Expected result: All defined permissions are returned, including the empty permission.
        """

        class TestPermission(PermissionBase):
            """
                A permission enumeration for testing.
            """

            EditUser = 1
            EditRole = 2
            EditGlobalSettings = 4

        expected_permissions = {
            TestPermission(0),
            TestPermission.EditUser,
            TestPermission.EditRole,
            TestPermission.EditGlobalSettings,
        }

        permissions = TestPermission.get_permissions(include_empty_permission=True)
        self.assertSetEqual(expected_permissions, permissions)

    def test_get_permissions_without_empty_permission_and_with_combinations(self) -> None:
        """
            Test getting all permissions, without the empty permission, but with combinations.

            Expected result: All defined permissions and all combinations of these permissions are returned, without
                             the empty permission.
        """

        class TestPermission(PermissionBase):
            """
                A permission enumeration for testing.
            """

            EditUser = 1
            EditRole = 2
            EditGlobalSettings = 4

        expected_permissions = {
            TestPermission.EditUser,
            TestPermission.EditRole,
            TestPermission.EditGlobalSettings,
            TestPermission.EditUser | TestPermission.EditRole,
            TestPermission.EditUser | TestPermission.EditGlobalSettings,
            TestPermission.EditRole | TestPermission.EditGlobalSettings,
            TestPermission.EditUser | TestPermission.EditRole | TestPermission.EditGlobalSettings,
        }

        permissions = TestPermission.get_permissions(all_combinations=True)
        self.assertSetEqual(expected_permissions, permissions)

    def test_get_permissions_with_empty_permission_and_with_combinations(self) -> None:
        """
            Test getting all permissions, with the empty permission and combinations.

            Expected result: All defined permissions and all combinations of these permissions are returned, including
                             the empty permission.
        """

        class TestPermission(PermissionBase):
            """
                A permission enumeration for testing.
            """

            EditUser = 1
            EditRole = 2
            EditGlobalSettings = 4

        expected_permissions = {
            TestPermission(0),
            TestPermission.EditUser,
            TestPermission.EditRole,
            TestPermission.EditGlobalSettings,
            TestPermission.EditUser | TestPermission.EditRole,
            TestPermission.EditUser | TestPermission.EditGlobalSettings,
            TestPermission.EditRole | TestPermission.EditGlobalSettings,
            TestPermission.EditUser | TestPermission.EditRole | TestPermission.EditGlobalSettings,
        }

        permissions = TestPermission.get_permissions(include_empty_permission=True, all_combinations=True)
        self.assertSetEqual(expected_permissions, permissions)

    def test_includes_permission(self):
        """
            Test checking if a permission includes another permission.

            Expected result: If the other permission is fully included in the permission, `True`.
        """

        class TestPermission(PermissionBase):
            """
                A permission enumeration for testing.
            """

            A = 1
            B = 2
            C = 4

        permission = TestPermission.A | TestPermission.B
        self.assertTrue(permission.includes_permission(TestPermission.A))
        self.assertTrue(permission.includes_permission(TestPermission.B))
        self.assertTrue(permission.includes_permission(permission))

        self.assertFalse(permission.includes_permission(TestPermission.C))
        self.assertFalse(permission.includes_permission(TestPermission.C | TestPermission.B))

    def test_includes_permission_does_not_include_other_permission_type(self):
        """
            Test checking if a permission includes another permission if the other permission is from a different
            permission class.

            Expected result: A type error is raised.
        """

        class TestPermission1(PermissionBase):
            """
                A permission enumeration for testing.
            """

            A = 1
            B = 2

        class TestPermission2(PermissionBase):
            """
                A permission enumeration for testing.
            """

            A = 1
            B = 2

        permission = TestPermission1.A | TestPermission1.B

        with self.assertRaises(TypeError) as exception_cm:
            permission.includes_permission(TestPermission2.A)

        self.assertEqual(str(exception_cm.exception),
                         'other_permission must be of type <enum \'Permission1\'>, but is <enum \'Permission2\'>')


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
