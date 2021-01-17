# -*- coding: utf-8 -*-

"""
    A collection of common types used in Aerarium.
"""

from typing import Callable
from typing import Tuple
from typing import Union

from flask import Response as Flask_Response
from werkzeug import Response as Werkzeug_Response


ResponseType = Union[Flask_Response, Werkzeug_Response, str, Tuple[str, int]]
"""
    The return type of view functions.
"""

ViewFunctionType = Callable[..., ResponseType]
"""
    The type of view functions with arbitrary parameters.
"""
