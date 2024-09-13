"User-facing API for validation"

from typing import Any, Tuple, Union, Type
from functools import wraps

from .common import CHECK_TYPES
from .utils import get_func_signatures
from .pytypes import TypeMismatchError, type_caster
from . import pytypes
from .typesystem import TypeSystem

def ensure_isa(obj, t, sampler=None):
    """Ensure 'obj' is of type 't'. Otherwise, throws a TypeError
    """
    t = type_caster.to_canon(t)
    t.validate_instance(obj, sampler)


def is_subtype(t1, t2):
    """Test if t1 is a subtype of t2
    """

    ct1 = type_caster.to_canon(t1)
    ct2 = type_caster.to_canon(t2)
    return ct1 <= ct2


def isa(obj: Any, t: Union[Type[Any], Tuple[Type[Any], ...]]) -> bool:
    """Tests if 'obj' is of type 't'

    Behaves like Python's isinstance, but supports the ``typing`` module and constraints.
    """
    ct = type_caster.to_canon(t)
    return ct.test_instance(obj)


def assert_isa(obj: Any, t: Union[Type[Any], Tuple[Type[Any], ...]]):
    """Ensure 'obj' is of type 't'. Otherwise, throws a TypeError

    Does nothing if Python is run with -O. (like the assert statement)
    """
    if CHECK_TYPES:
        try:
            ensure_isa(obj, t)
        except TypeMismatchError as e:
            item_value, item_type = e.args
            msg = f"Expected value of type '{t}', instead got '{obj!r}'."
            if item_value is not obj:
                msg += f"\n\n    Failed on item: '{item_value!r}', expected type '{item_type}'."
            raise TypeError(msg)



def issubclass(t1: Type[Any], t2: Union[Type[Any], Tuple[Type[Any], ...]]) -> bool:
    """Test if t1 is a subclass of t2

    Parameters:
        t1 - a type
        t2 - a type or a tuple of types

    Behaves like Python's issubclass, but supports the ``typing`` module.
    """
    if isinstance(t2, tuple):
        return any(is_subtype(t1, i) for i in t2)
    return is_subtype(t1, t2)


class PythonTyping(TypeSystem):
    isinstance = staticmethod(isa)
    issubclass = staticmethod(issubclass)
    to_canonical_type = type_caster.to_canon
    get_type = type
    default_type = pytypes.All
    any_type = pytypes.Any


def validate_func(f):
    """Decorator to validate the argument types when calling the decorated function.

    Parameters:
        f - function to validate

    Note: Keyword arguments currently will not be validated!
          This might be added in the future.
    """
    sigs = {len(s): s for s in get_func_signatures(PythonTyping, f)}

    @wraps(f)
    def _inner(*args, **kwargs):
        sig = sigs[len(args)]
        assert len(sig) == len(args)
        try:
            for a, s in zip(args, sig):
                assert_isa(a, s)
        except TypeError as e:
            raise TypeError(f"Validation failed when calling {f} - {e}") from e

        return f(*args, **kwargs)

    return _inner

