#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app.userprofile import Permission


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

    def test_bitwise_and_success(self):
        """
            Test the bitwise and method.

            Expected result: The method returns the same result as performing the operation manually.
        """

        expectation = Permission.EditRole
        result = Permission.bitwise_and(Permission.EditRole)
        self.assertEqual(expectation, result)

        combination = Permission.EditRole | Permission.EditGlobalSettings
        expectation = combination & Permission.EditUser
        result = Permission.bitwise_and(combination, Permission.EditUser)
        self.assertEqual(expectation, result)

        combination_1 = Permission.EditGlobalSettings | Permission.EditRole | Permission.EditUser
        combination_2 = Permission.EditGlobalSettings | Permission.EditRole
        combination_3 = Permission.EditGlobalSettings | Permission.EditUser

        expectation = combination_1 & combination_2 & combination_3
        result = Permission.bitwise_and(combination_1, combination_2, combination_3)
        self.assertEqual(expectation, result)

    def test_bitwise_and_failure(self):
        """
            Test the bitwise and method with an invalid permission..

            Expected result: The method raises an error.
        """
        with self.assertRaises(ValueError) as exception_cm:
            # noinspection PyTypeChecker
            Permission.bitwise_and(Permission.EditGlobalSettings, None, Permission.EditRole)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))

    def test_bitwise_or_success(self):
        """
            Test the bitwise or method.

            Expected result: The method returns the same result as performing the operation manually.
        """

        expectation = Permission.EditRole
        result = Permission.bitwise_or(Permission.EditRole)
        self.assertEqual(expectation, result)

        expectation = Permission.EditRole | Permission.EditUser
        result = Permission.bitwise_or(Permission.EditRole, Permission.EditUser)
        self.assertEqual(expectation, result)

        expectation = Permission.EditRole | Permission.EditUser | Permission.EditGlobalSettings
        result = Permission.bitwise_or(Permission.EditRole, Permission.EditUser, Permission.EditGlobalSettings)
        self.assertEqual(expectation, result)

    def test_bitwise_or_failure(self):
        """
            Test the bitwise or method with an invalid permission.

            Expected result: The method raises an error.
        """
        with self.assertRaises(ValueError) as exception_cm:
            # noinspection PyTypeChecker
            Permission.bitwise_or(Permission.EditGlobalSettings, None, Permission.EditRole)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))

    def test_bitwise_xor_success(self):
        """
            Test the bitwise xor method.

            Expected result: The method returns the same result as performing the operation manually.
        """

        expectation = Permission.EditRole
        result = Permission.bitwise_xor(Permission.EditRole)
        self.assertEqual(expectation, result)

        expectation = Permission.EditRole | Permission.EditUser
        result = Permission.bitwise_xor(Permission.EditRole, Permission.EditUser)
        self.assertEqual(expectation, result)

        expectation = Permission.EditRole | Permission.EditUser | Permission.EditGlobalSettings
        result = Permission.bitwise_xor(Permission.EditRole, Permission.EditUser, Permission.EditGlobalSettings)
        self.assertEqual(expectation, result)

        combination_1 = Permission.EditRole | Permission.EditGlobalSettings
        combination_2 = Permission.EditGlobalSettings | Permission.EditRole
        expectation = combination_1 ^ combination_2
        result = Permission.bitwise_xor(combination_1, combination_2)
        self.assertEqual(expectation, result)

        combination_1 = Permission.EditRole | Permission.EditGlobalSettings
        combination_2 = Permission.EditGlobalSettings | Permission.EditRole
        expectation = combination_1 ^ combination_2 ^ Permission.EditUser
        result = Permission.bitwise_xor(combination_1, combination_2, Permission.EditUser)
        self.assertEqual(expectation, result)

    def test_bitwise_xor_failure(self):
        """
            Test the bitwise or method with an invalid permission.

            Expected result: The method raises an error.
        """
        with self.assertRaises(ValueError) as exception_cm:
            # noinspection PyTypeChecker
            Permission.bitwise_xor(Permission.EditGlobalSettings, None, Permission.EditRole)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))
