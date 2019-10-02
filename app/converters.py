# -*- coding: utf-8 -*-

"""
    Collection of converters.
"""

from datetime import timedelta


def timedelta_to_minutes(delta: timedelta) -> int:
    """
        Get the time delta in full minutes, without remaining seconds.

        :param delta: The time delta to get in minutes.
        :return: The delta in minutes, without partial minutes.
    """

    return int(delta.total_seconds() // 60)
