from typing import Any, Union, Callable, List, Dict, Tuple
from contextlib import suppress

from .common import CHECK_TYPES
from .typesystem import TypeSystem, PythonBasic
from .dispatch import MultiDispatch
from .pytypes import ensure_isa, TypeMistmatchError

dp = MultiDispatch(PythonBasic())


def _isinstance(a, b):
    try:
        return isinstance(a, b)
    except TypeError as e:
        raise TypeError(f"Bad arguments to isinstance: {a}, {b}") from e

_orig_issubclass = issubclass
def _issubclass(a, b):
    try:
        return _orig_issubclass(a, b)
    except TypeError as e:
        raise TypeError(f"Bad arguments to issubclass: {a}, {b}") from e


class SubclassDispatch(PythonBasic):
    isinstance = issubclass

dp_type = MultiDispatch(SubclassDispatch())

def switch_subclass(t, d):
    for k, v in d.items():
        if _issubclass(t, k):
            return v




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
    if t2 is Any:
        return True

    t1 = canonize_type(t1)

    if isinstance(t1, tuple):
        return all(issubclass(t, t2) for t in t1)
    elif isinstance(t2, tuple):
        return any(issubclass(t1, t) for t in t2)

    if hasattr(t2, '__origin__'):
        t2 = canonize_type(t2)
        return t1 == t2    # TODO add some clever logic here
    elif hasattr(t1, '__origin__'):
        return issubclass(t1.__origin__, t2)    # XXX more complicated than that?

    return _issubclass(t1, t2)



class PythonTyping(TypeSystem):
    isinstance = staticmethod(isa)
    issubclass = staticmethod(issubclass)
    canonize_type = staticmethod(canonize_type)
    get_type = type
    default_type = object