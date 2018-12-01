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

    def test_bitwise_and(self):
        """
            Test the bitwise or method.

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

    def test_bitwise_or(self):
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
