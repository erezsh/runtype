"User-facing API for validation"

from typing import Any, Dict, List, Tuple

from .common import CHECK_TYPES
from .pytypes import TypeMismatchError, cast_to_type
from .typesystem import TypeSystem


def ensure_isa(obj, t, sampler=None):
    """Ensure 'obj' is of type 't'. Otherwise, throws a TypeError
    """
    t = cast_to_type(t)
    t.validate_instance(obj, sampler)


def is_subtype(t1, t2):
    """Test if t1 is a subtype of t2
    """

    t1 = cast_to_type(t1)
    t2 = cast_to_type(t2)
    return t1 <= t2


def isa(obj, t):
    """Tests if 'obj' is of type 't'

    Behaves like Python's isinstance, but supports the ``typing`` module and constraints.
    """
    try:
        ensure_isa(obj, t)
        return True
    except TypeMismatchError as e:
        return False


def assert_isa(obj, t):
    """Ensure 'obj' is of type 't'. Otherwise, throws a TypeError

    Does nothing if Python is run with -O. (like the assert statement)
    """
    if CHECK_TYPES:
        try:
            ensure_isa(obj, t)
        except TypeMismatchError as e:
            item_value, item_type = e.args
            msg = f"Expected value of type {t}, instead got {obj!r}"
            if item_value is not obj:
                msg += f'\n\n    Failed on item: {item_value!r}, expected type {item_type}'
            raise TypeError(msg)


def canonize_type(t):
    "Turns List -> list, Dict -> dict, etc."
    try:
        return {
            Any: object,
            List: list,
            Dict: dict,
            Tuple: tuple,
            List[Any]: list,
            Dict[Any, Any]: dict,
            Tuple[Any]: tuple,
        }[t]
    except KeyError:
        return t


def issubclass(t1, t2):
    """Test if t1 is a subclass of t2

    Parameters:
        t1 - a type
        t2 - a type or a tuple of types

    Behaves like Python's issubclass, but supports the ``typing`` module.
    """
    if isinstance(t2, tuple):
        return any(issubclass(t1, i) for i in t2)
    return is_subtype(t1, t2)


class PythonTyping(TypeSystem):
    isinstance = staticmethod(isa)
    issubclass = staticmethod(issubclass)
    canonize_type = staticmethod(canonize_type)
    get_type = type
    default_type = object

