# -*- coding: utf-8 -*-

from unittest import TestCase

from app.tools.math import is_power_of_two


class MathTest(TestCase):

    def test_is_power_of_two_failure(self):
        """
            Test if number that are not a power of two are a power of 2.

            Expected Result: `False`.
        """

        # Non-positive numbers are not a power of two.
        self.assertFalse(is_power_of_two(0))
        self.assertFalse(is_power_of_two(-4))

        # Numbers that are not a power of 2.
        self.assertFalse(is_power_of_two(2 ** 9 - 1))

    def test_is_power_of_two_success(self):
        """
            Test if a power of 2 is a power of 2.

            Expected Result: `True`.
        """

        self.assertTrue(is_power_of_two(2 ** 9))
