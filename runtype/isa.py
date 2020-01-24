from typing import _GenericAlias as TypeBase, Any, Union, Callable, List, Dict, Tuple

from .typesystem import TypeSystem, PythonBasic
from .dispatch import MultiDispatch

dp = MultiDispatch(PythonBasic)

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

@dp
def isa(obj, t):
    if t is Any or t == (Any,):
        return True
    return _isinstance(obj, t)

@dp
def isa(obj, t: tuple):
    return any(isa(obj, opt) for opt in t)

@dp
def isa(obj, t: TypeBase):
    if t.__origin__ is list:
        return all(isa(item, t.__args__) for item in obj)
    elif t.__origin__ is tuple:
        if not (isinstance(obj, tuple) and len(t.__args__) == len(obj)):
            return False
        return all(isa(a, b) for a, b in zip(obj, t.__args__))
    elif t.__origin__ is dict:
        kt, vt = t.__args__
        return all(isa(k, kt) and isa(v, vt) for k, v in obj.items())
    elif t.__origin__ is Union:
        return isa(obj, t.__args__)
    elif _issubclass(t, Callable):
        return callable(obj)
    assert False, t


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
        if isinstance(t, TypeBase):
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

    if isinstance(t2, TypeBase):
        t2 = canonize_type(t2)
        return t1 == t2    # TODO add some clever logic here
    elif isinstance(t1, TypeBase):
        return issubclass(t1.__origin__, t2)    # XXX more complicated than that?

    return _issubclass(t1, t2)



class PythonTyping(TypeSystem):
    isinstance = staticmethod(isa)
    issubclass = staticmethod(issubclass)
    canonize_type = staticmethod(canonize_type)
    get_type = type