# -*- coding: utf-8 -*-

from datetime import timedelta

from unittest import TestCase

from app import timedelta_to_minutes


class ConvertersTest(TestCase):

    def test_timedelta_to_minutes(self):
        """
            Test converting a timedelta object to minutes.

            Expected Result: The delta without seconds is returned as an integer.
        """

        minutes = 42
        seconds = 55
        delta = timedelta(minutes=minutes, seconds=seconds)

        delta_minutes = timedelta_to_minutes(delta)
        self.assertEqual(minutes, delta_minutes)
