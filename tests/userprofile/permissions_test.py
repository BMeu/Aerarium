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
