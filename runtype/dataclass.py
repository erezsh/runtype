from copy import copy
import dataclasses

from .common import CHECK_TYPES
from .isa import ensure_isa as default_ensure_isa, TypeMistmatchError

def _post_init(self, ensure_isa):
    for name, field in getattr(self, '__dataclass_fields__', {}).items():
        value = getattr(self, name)
        try:
            ensure_isa(value, field.type)
        except TypeMistmatchError as e:
            item_value, item_type = e.args
            msg = f"[{type(self).__name__}] Attribute '{name}' expected value of type {field.type}, instead got {value!r}"
            if item_value is not value:
                msg += f'\n\n    Failed on item: {item_value}, expected type {item_type}'
            raise TypeError(msg)


def _setattr(self, name, value, ensure_isa):
    try:
        field = self.__dataclass_fields__[name]
    except (KeyError, AttributeError):
        pass
    else:
        ensure_isa(value, field.type)


def replace(self, **kwargs):
    """Returns a new instance, with the given attibutes and values overwriting the existing ones.

    Useful for making copies with small updates.

    Examples:
        >>> @dataclass
        ... class A:
        ...     a: int
        ...     b: int
        >>> A(1, 2).replace(a=-2)
        A(a=-2, b=2)

        >>> some_instance.replace() == copy(some_instance)   # Equivalent operations
        True
    """
    return dataclasses.replace(self, **kwargs)

def __iter__(self):
    "Yields a list of tuples [(name, value), ...]"
    return ((name, getattr(self, name)) for name in self.__dataclass_fields__)

def aslist(self):
    """Returns a list of values

    Equivalent to: list(dict(this).values())
    """
    return [getattr(self, name) for name in self.__dataclass_fields__]

def astuple(self):
    """Returns a tuple of values

    Equivalent to: tuple(dict(this).values())
    """
    return tuple(getattr(self, name) for name in self.__dataclass_fields__)


def _set_if_not_exists(cls, d):
    for attr, value in d.items():
        try:
            getattr(cls, attr)
        except AttributeError:
            setattr(cls, attr, value)


def _process_class(cls, ensure_isa, check_types, **kw):
    if check_types:
        c = copy(cls)

        orig_post_init = getattr(cls, '__post_init__', None)
        def __post_init__(self):
            _post_init(self, ensure_isa=ensure_isa)
            if orig_post_init is not None:
                orig_post_init(self)
        c.__post_init__ = __post_init__

        if not kw['frozen']:
            orig_set_attr = getattr(cls, '__setattr__')
            def __setattr__(self, name, value):
                _setattr(self, name, value, ensure_isa=ensure_isa)
                orig_set_attr(self, name, value)
            c.__setattr__ = __setattr__
    else:
        c = cls

    _set_if_not_exists(c, {
        'replace': replace,
        'aslist': aslist,
        'astuple': astuple,
        '__iter__': __iter__,
    })
    return dataclasses.dataclass(c, **kw)


def dataclass(cls=None, *, ensure_isa=default_ensure_isa, check_types=CHECK_TYPES, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=True):
    """runtype.dataclass is a drop-in replacement, that adds functionality on top of Python's built-in dataclass.

    * Adds run-time type validation
    * Adds convenience methods:
        * replace - create a new instance, with updated attributes
        * aslist - returns the dataclass values as a list
        * astuple - returns the dataclass values as a tuple
        * dict(this) - returns a dict of the dataclass attributes and values
    * Frozen by default. Can be disabled (not recommended)

    Note: Changes to an existing instance (i.e. by setting attributes) are not validated!
          Use `frozen=False` at your own risk.

    Example:
        >>> @dataclass
        >>> class Point:
        ...     x: int
        ...     y: int

        >>> p = Point(2, 3)
        >>> p
        Point(x=2, y=3)
        >>> dict(p)         # Maintains order
        {'x': 2, 'y': 3}

        >>> p.replace(x=30)  # New instance
        Point(x=30, y=3)
    """

    def wrap(cls):
        return _process_class(cls, ensure_isa, check_types, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)
