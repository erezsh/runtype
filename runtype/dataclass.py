from copy import copy
import dataclasses

from .common import CHECK_TYPES
from .isa import TypeMismatchError, ensure_isa as default_ensure_isa
from .pytypes import cast_to_type, SumType, NoneType

Required = object()


class Configuration:
    """Generic configuration template"""

    def canonize_type(self, t):
        return t

    def on_assign_none(self, t):
        return t

    def ensure_isa(self, a, b):
        raise NotImplementedError()

    def cast(self, d, to_type):
        raise NotImplementedError()


class PythonConfiguration(Configuration):
    """Configuration to support Mypy-like and Pydantic-like features
    """
    def canonize_type(self, t):
        return cast_to_type(t)

    def ensure_isa(self, a, b):
        return default_ensure_isa(a, b)

    def cast(self, obj, to_type):
        return to_type.cast_from(obj)

    def on_assign_none(self, type_):
        return SumType([type_, NoneType])



def _post_init(self, config, should_cast):
    for name, field in getattr(self, '__dataclass_fields__', {}).items():
        value = getattr(self, name)

        if value is Required:
            raise TypeError(f"Field {name} requires a value")

        try:
            if should_cast:    # Basic cast
                value = config.cast(value, field.type)
                object.__setattr__(self, name, value)
            else:
                config.ensure_isa(value, field.type)
        except TypeMismatchError as e:
            item_value, item_type = e.args
            msg = f"[{type(self).__name__}] Attribute '{name}' expected value of type {field.type}."
            msg += f" Instead got {value!r}"
            if item_value is not value:
                msg += f'\n\n    Failed on item: {item_value!r}, expected type {item_type}'
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


def json(self):
    """Returns a JSON of values, going recursively into other objects (if possible)"""
    return {
        k: json(v) if dataclasses.is_dataclass(v) else v
        for k, v in self
    }


def _set_if_not_exists(cls, d):
    for attr, value in d.items():
        try:
            getattr(cls, attr)
        except AttributeError:
            setattr(cls, attr, value)


def _process_class(cls, config, check_types, **kw):
    for name, type_ in getattr(cls, '__annotations__', {}).items():
        type_ = config.canonize_type(type_)

        default = getattr(cls, name, Required)
        if isinstance(default, (list, dict, set)):
            def f(_=default):
                return copy(_)
            setattr(cls, name, dataclasses.field(default_factory=f))

        elif default is Required:
            setattr(cls, name, Required)

        elif default is None:
            type_ = config.on_assign_none(type_)

        cls.__annotations__[name] = type_

    if check_types:
        c = copy(cls)

        orig_post_init = getattr(cls, '__post_init__', None)

        def __post_init__(self):
            _post_init(self, config=config, should_cast=check_types == 'cast')
            if orig_post_init is not None:
                orig_post_init(self)

        c.__post_init__ = __post_init__

        if not kw['frozen']:
            orig_set_attr = getattr(cls, '__setattr__')

            def __setattr__(self, name, value):
                _setattr(self, name, value, ensure_isa=config.ensure_isa)
                orig_set_attr(self, name, value)

            c.__setattr__ = __setattr__
    else:
        c = cls

    _set_if_not_exists(c, {
        'replace': replace,
        'aslist': aslist,
        'astuple': astuple,
        'json': json,
        '__iter__': __iter__,
    })
    return dataclasses.dataclass(c, **kw)


def dataclass(cls=None, *, config: Configuration = PythonConfiguration(),
                           check_types: bool = CHECK_TYPES,
                           init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=True):
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
    assert isinstance(config, Configuration)

    def wrap(cls):
        return _process_class(cls, config, check_types,
                              init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)
