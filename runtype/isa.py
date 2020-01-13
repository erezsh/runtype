from typing import _GenericAlias as TypeBase, Any, Union, Callable, List, Dict, Tuple

def _isinstance(a, b):
    try:
        return isinstance(a, b)
    except TypeError as e:
        raise TypeError(f"Bad arguments to isinstance: {a}, {b}") from e

def _issubclass(a, b):
    try:
        return issubclass(a, b)
    except TypeError as e:
        raise TypeError(f"Bad arguments to issubclass: {a}, {b}") from e

def isa(obj, t):
    if t is Any or t == (Any,):
        return True
    elif isinstance(t, tuple):
        return any(isa(obj, opt) for opt in t)
    elif isinstance(t, TypeBase):
        if t.__origin__ is list:
            return all(isa(item, t.__args__) for item in obj)
        elif t.__origin__ is dict:
            kt, vt = t.__args__
            return all(isa(k, kt) and isa(v, vt) for k, v in obj.items())
        elif t.__origin__ is Union:
            return isa(obj, t.__args__)
        elif issubclass(t, Callable):
            return callable(obj)
        assert False, t.__origin__
    return _isinstance(obj, t)



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

def test_subclass(t1, t2):
    if t2 is Any:
        return True

    t1 = canonize_type(t1)
    if isinstance(t1, tuple):
        return all(test_subclass(t, t2) for t in t1)

    if isinstance(t2, tuple):
        return any(test_subclass(t1, t) for t in t2)
    elif isinstance(t2, TypeBase):
        t2 = canonize_type(t2)

    return _issubclass(t1, t2)