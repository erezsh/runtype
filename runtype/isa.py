from typing import _GenericAlias as TypeBase, Any, Union, Callable, List, Dict, Tuple

from .common import CHECK_TYPES
from .typesystem import TypeSystem, PythonBasic
from .dispatch import MultiDispatch

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


class RuntypeError(TypeError):
    pass

class TypeMistmatchError(RuntypeError):
    pass

class TupleLengthError(TypeMistmatchError):
    pass


@dp
def ensure_isa(obj, t):
    if t is Any or t == (Any,):
        return
    if not _isinstance(obj, t):
        raise TypeMistmatchError(obj, t)

@dp
def ensure_isa(obj, t: tuple):
    if not any(isa(obj, opt) for opt in t):
        raise TypeMistmatchError(obj, t)

@dp
def ensure_isa(obj, t: TypeBase):
    if t.__origin__ is list:
        ensure_isa(obj, list)
        for item in obj:
            ensure_isa(item, t.__args__)
    elif t.__origin__ is set:
        ensure_isa(obj, set)
        for item in obj:
            ensure_isa(item, t.__args__)
    elif t.__origin__ is tuple:
        ensure_isa(obj, tuple)
        if len(obj) != len(t.__args__):
            raise TupleLengthError(obj, t.__args__)
        for item, type_ in zip(obj, t.__args__):
            ensure_isa(item, type_)
    elif t.__origin__ is dict:
        ensure_isa(obj, dict)
        kt, vt = t.__args__
        for k, v in obj.items():
            ensure_isa(k, kt)
            ensure_isa(v, vt)
    elif t.__origin__ is Union:
        ensure_isa(obj, t.__args__)    # Send as tuple
    elif _issubclass(t, Callable):
        if not callable(obj):
            raise TypeMistmatchError(obj, callable)
    else:
        assert False, t



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
    default_type = object