from typing import Any, Union, Callable, List, Dict, Tuple
from contextlib import suppress

from .common import CHECK_TYPES
from .typesystem import TypeSystem, PythonBasic
from .dispatch import MultiDispatch
from .pytypes import cast_to_type, TypeMistmatchError


def ensure_isa(obj, t):
    t = cast_to_type(t)
    t.validate_instance(obj)

def is_subtype(t1, t2):
    t1 = cast_to_type(t1)
    t2 = cast_to_type(t2)
    return t1 <= t2

def isa(obj, t):
    try:
        ensure_isa(obj, t)
        return True
    except TypeMistmatchError as e:
        return False


def assert_isa(obj, t):
    if CHECK_TYPES:
        try:
            ensure_isa(obj, t)
        except TypeMistmatchError as e:
            item_value, item_type = e.args
            msg = f"Expected value of type {t}, instead got {obj!r}"
            if item_value is not obj:
                msg += f'\n\n    Failed on item: {item_value}, expected type {item_type}'
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
        with suppress(AttributeError):
            if t.__origin__ is Union:
                return t.__args__
        return t

def issubclass(t1, t2):
    return is_subtype(t1, t2)


class PythonTyping(TypeSystem):
    isinstance = staticmethod(isa)
    issubclass = staticmethod(issubclass)
    canonize_type = staticmethod(canonize_type)
    get_type = type
    default_type = object