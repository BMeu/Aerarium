# -*- coding: utf-8 -*-

"""
    A collection of generally useful mathematical (or numerical) functions.
"""


def is_power_of_two(value: int) -> bool:
    """
        Determine if the given value is a power of 2.

        Negative numbers and 0 cannot be a power of 2 and will thus return `False`.

        :param value: The value to check.
        :return: `True` if the value is a power of two, 0 otherwise.
    """

    if value <= 0:
        return False

    # If value is a power of two, its highest bit that is set to 1 will toggle to 0 when subtracting 1 because all
    # other bits are 0; all other bits will thus be flipped to 1. Therefore, value and (value - 1) don't have any bits
    # in common and the bitwise AND will return 0.
    # On the other hand, if value is not a power of two, the highest bit set to 1 will not be flipped when subtracting 1
    # and thus, value and (value - 1) will have bits in common and the bitwise AND will not return 0.
    # Therefore, if the result is 0, value is a power of two.
    return (value & (value - 1)) == 0
