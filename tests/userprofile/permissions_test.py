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
