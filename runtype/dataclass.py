"""
Enhances Python's built-in dataclass, with type-checking and extra ergonomics.
"""

import random
from copy import copy
import dataclasses
from typing import Union, Any, Callable, TypeVar, Dict, Optional, overload
from typing import TYPE_CHECKING, ClassVar, Type
from abc import ABC, abstractmethod
import inspect
import types
import warnings

if TYPE_CHECKING:
    from typing_extensions import dataclass_transform
else:
    def dataclass_transform(*a, **kw):
        return lambda f:f

from .utils import ForwardRef
from .common import CHECK_TYPES
from .validation import TypeMismatchError, ensure_isa as default_ensure_isa
from .pytypes import TypeCaster, SumType, NoneType, ATypeCaster, PythonType, type_caster

Required = object()
MAX_SAMPLE_SIZE = 16

class NopTypeCaster(ATypeCaster):
    cache: Dict[int,Union[PythonType, type]] = {}
    def to_canon(self, t):
        return t

class Configuration(ABC):
    """Generic configuration template for dataclass. Mainly for type-checking.

    To modify dataclass behavior, inherit and extend this class,
    and pass it to the `dataclass()` function as the ``config`` parameter.
    (parameter ``check_types`` must be nonzero)

    Example:
        ::

            class IsMember(Configuration):
                @staticmethod
                def ensure_isa(a, b):
                    if a not in b:
                        raise TypeError(f"{a} is not in {b}")

            @dataclass(config=IsMember())
            class Form:
                answer1: ("yes", "no")
                score: range(1, 11)

            ...

            >>> Form("no", 3)
            Form(answer1='no', score=3)

            >>> Form("no", 12)
            Traceback (most recent call last):
                ...
            TypeError: 12 is not in range(1, 11)

    """

    field_types = (dataclasses.Field,)

    def on_default(self, default):
        """Called whenever a dataclass member is assigned a default value.
        """
        return default

    def make_type_caster(self, frame) -> ATypeCaster:
        """Return a type caster, as defined in pytypes.TypeCaster
        """
        return NopTypeCaster()

    @abstractmethod
    def ensure_isa(self, a, b, sampler=None):
        """Ensure that 'a' is an instance of type 'b'. If not, raise a TypeError.
        """

    @abstractmethod
    def cast(self, obj, t):
        """Attempt to cast 'obj' to type 't'. If such a cast is not possible, raise a TypeError.

        The result is expected to pass `self.ensure_isa(res, t)` without an error,
        however this assertion is not validated, for performance reasons.
        """


class PythonConfiguration(Configuration):
    """Configuration to support Mypy-like and Pydantic-like features

    This is the default class given to the ``dataclass()`` function.
    """
    
    def make_type_caster(self, frame: Optional[types.FrameType]):
        return TypeCaster(frame)

    ensure_isa = staticmethod(default_ensure_isa)

    def cast(self, obj, to_type):
        return to_type.cast_from(obj)

    def on_default(self, default):
        if isinstance(default, (list, dict, set)):
            def f(_=default):
                return copy(_)
            return dataclasses.field(default_factory=f)
        elif isinstance(default, self.field_types):
            d = default.default
            if isinstance(d, (list, dict, set)):
                def f(_=d):
                    return copy(_)
                default.default = dataclasses.MISSING
                default.default_factory = f
        return default


def _get_field_type(type_caster, field):
    try:
        return type_caster.cache[id(field)]
    except KeyError:
        type_ = field.type
        if isinstance(type_, str):
            type_ = ForwardRef(type_)
        type_ = type_caster.to_canon(type_)
        if field.default is None:
            type_ = SumType([type_, NoneType])
        type_caster.cache[id(field)] = type_
        return type_

def _validate_attr(config, should_cast, sampler, obj, name, type_, value):
    try:
        if should_cast:    # Basic cast
            assert not sampler
            try:
                config.ensure_isa(value, type_, sampler)
                return value
            except TypeMismatchError:
                return config.cast(value, type_)
        else:
            config.ensure_isa(value, type_, sampler)
    except TypeMismatchError as e:
        item_value, item_type = e.args
        msg = f"[{type(obj).__name__}] Attribute '{name}' expected a value of type '{type_}'."
        msg += f" Instead got type '{type(value).__name__}', with value {value!r}."
        if item_value is not value:
            msg += f'\n\n    Failed on item: {item_value!r}, expected type {item_type}'
        raise TypeError(msg)

def _post_init(self, config, should_cast, sampler, type_caster):
    for name, field in getattr(self, '__dataclass_fields__', {}).items():
        value = getattr(self, name)

        if value is Required:
            raise TypeError(f"Field {name} requires a value")

        type_ = _get_field_type(type_caster, field)
        new_value = _validate_attr(config, should_cast, sampler, self, name, type_, value)
        if new_value is not None:
            object.__setattr__(self, name, new_value)

def _post_init__no_check_types(self):
    for name, field in getattr(self, '__dataclass_fields__', {}).items():
        value = getattr(self, name)

        if value is Required:
            raise TypeError(f"Field {name} requires a value")

def _setattr(obj, setattr, name, value, config, should_cast, sampler, type_caster):
    try:
        field = obj.__dataclass_fields__[name]
    except (KeyError, AttributeError):
        new_value = None
    else:
        type_ = _get_field_type(type_caster, field)
        new_value = _validate_attr(config, should_cast, sampler, obj, name, type_, value)
    setattr(obj, name, value if new_value is None else new_value)


def replace(inst, **kwargs):
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
    return dataclasses.replace(inst, **kwargs)


def __iter__(inst):
    "Yields a list of tuples [(name, value), ...]"
    warnings.warn("This method is deprecated and will be removed in future versions."
                  "Please use `.asdict()` or `.asitems()` instead.", DeprecationWarning)
    return ((name, getattr(inst, name)) for name in inst.__dataclass_fields__)

def asdict(inst):
    """Returns a dict of {name: value, ...}
    """
    return {name: getattr(inst, name) for name in inst.__dataclass_fields__}

def asitems(inst):
    "Yields a list of tuples [(name, value), ...]"
    return ((name, getattr(inst, name)) for name in inst.__dataclass_fields__)

def aslist(inst):
    """Returns a list of the values
    """
    return [getattr(inst, name) for name in inst.__dataclass_fields__]


def astuple(inst):
    """Returns a tuple of the values
    """
    return tuple(getattr(inst, name) for name in inst.__dataclass_fields__)


def _json_rec(inst):
    if dataclasses.is_dataclass(inst):
        return json(inst)
    elif isinstance(inst, (list, set, frozenset, tuple)):
        return [_json_rec(i) for i in inst]
    elif isinstance(inst, dict):
        return {k:_json_rec(v) for k, v in inst.items()}
    return inst

def json(inst):
    """Returns a JSON of values, going recursively into other objects (if possible)"""
    return {
        k: _json_rec(v)
        for k, v in inst.asitems()
    }

def _set_if_not_exists(cls, d):
    for attr, value in d.items():
        try:
            getattr(cls, attr)
        except AttributeError:
            setattr(cls, attr, value)


def _sample(seq, max_sample_size=MAX_SAMPLE_SIZE):
    if len(seq) <= max_sample_size:
        return seq
    return random.sample(seq, max_sample_size)

def _process_class(cls: type, config: Configuration, check_types, context_frame, **kw):

    for name, type_ in getattr(cls, '__annotations__', {}).items():
        # type_ = config.type_to_canon(type_) if not isinstance(type_, str) else type_

        # If default not specified, assign Required, for a later check
        # We don't assign MISSING; we want to bypass dataclass which is too strict for this
        default = getattr(cls, name, Required)
        if default is Required:
            setattr(cls, name, Required)
        elif default is not dataclasses.MISSING:
            if isinstance(default, config.field_types):
                if default.default is dataclasses.MISSING and default.default_factory is dataclasses.MISSING:
                    default.default = Required

            new_default = config.on_default(default)
            if new_default is not default:
                setattr(cls, name, new_default)


        cls.__annotations__[name] = type_


    c = copy(cls)
    orig_post_init = getattr(cls, '__post_init__', None)

    init_f = getattr(c, '__init__', None)
    if init_f:
        try:
            del c.__init__
        except AttributeError:
            pass
        init_dispatcher = getattr(init_f, '__dispatcher__', None)
    else:
        init_dispatcher = None

    if check_types:
        sampler = _sample if check_types=='sample' else None
        type_caster = config.make_type_caster(context_frame)
        should_cast = check_types == 'cast'

        def __post_init__(self):
            # Only now context_frame has complete information
            _post_init(self, config=config, should_cast=should_cast, sampler=sampler, type_caster=type_caster)
            if orig_post_init is not None:
                orig_post_init(self)

        c.__post_init__ = __post_init__

        if not kw['frozen']:
            orig_set_attr = getattr(cls, '__setattr__')

            def __setattr__(self, name, value):
                _setattr(self, orig_set_attr, name, value, config, should_cast, sampler, type_caster)

            c.__setattr__ = __setattr__
    else:
        def __post_init__(self):
            _post_init__no_check_types(self)
            if orig_post_init is not None:
                orig_post_init(self)

        c.__post_init__ = __post_init__

    _set_if_not_exists(c, {
        'replace': replace,
        'asdict': asdict,
        'asitems': asitems,
        'aslist': aslist,
        'astuple': astuple,
        'json': json,
        '__iter__': __iter__,
    })

    slots = kw.pop('slots')
    c = dataclasses.dataclass(c, **kw)
    if slots:
        c = _add_slots(c, kw['frozen'])
    
    if init_dispatcher:
        assert init_f
        # __init__ may have been generated by the dataclass function
        if hasattr(c, '__init__'):
            # We will add it to the dispatch
            c.__init__ = init_dispatcher(c.__init__)
        else:
            c.__init__ = init_f
    return c


def _dataclass_getstate(self):
    return [getattr(self, f.name) for f in dataclasses.fields(self)]

def _dataclass_setstate(self, state):
    for field, value in zip(dataclasses.fields(self), state):
        # use setattr because dataclass may be frozen
        object.__setattr__(self, field.name, value)

def _add_slots(cls, is_frozen):
    # Taken from official dataclasses implementation (3.10)
    # Need to create a new class, since we can't set __slots__ after a class has been created.

    cls_dict = dict(cls.__dict__)
    field_names = tuple(f.name for f in dataclasses.fields(cls))
    cls_dict['__slots__'] = field_names
    for field_name in field_names:
        # Remove our attributes, if present. They'll still be available in _MARKER.
        cls_dict.pop(field_name, None)

    # Remove __dict__ itself.
    cls_dict.pop('__dict__', None)

    # And finally create the class.
    qualname = getattr(cls, '__qualname__', None)
    cls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
    if qualname is not None:
        cls.__qualname__ = qualname

    if is_frozen:
        # Need this for pickling frozen classes with slots.
        cls.__getstate__ = _dataclass_getstate
        cls.__setstate__ = _dataclass_setstate

    return cls


_T = TypeVar('_T')
python_config = PythonConfiguration()

@dataclass_transform(field_specifiers=(dataclasses.field, dataclasses.Field), frozen_default=True)
@overload
def dataclass(
    *,
    check_types: Union[bool, str] = CHECK_TYPES,
    config: Configuration = python_config,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = True,
    slots: bool = ...,
) -> Callable[[Type[_T]], Type[_T]]: ...

@dataclass_transform(field_specifiers=(dataclasses.field, dataclasses.Field), frozen_default=True)
@overload
def dataclass(_cls: Type[_T]) -> Type[_T]: ...

@dataclass_transform(field_specifiers=(dataclasses.field, dataclasses.Field), frozen_default=True)
def dataclass(cls: Optional[Type[_T]]=None, *,
              check_types: Union[bool, str] = CHECK_TYPES,
              config: Configuration = python_config,
                init: bool = True,
                repr: bool = True,
                eq: bool = True,
                order: bool = False,
                unsafe_hash: bool = False,
                frozen: bool = True,
                slots: bool = ...,
    ) -> type:

    """Runtype's dataclass is a drop-in replacement to Python's built-in dataclass, with added functionality.

    **Differences from builtin dataclass:**

    1. Type validation
      - Adds run-time type validation (when check_types is nonzero)
      - Performs automatic casting (when check_types == 'cast')

    2. Ergonomics
      - Supports assigning mutable literals (i.e. list, set, and dict). Each instance gets a new copy.
      - Adds convenience methods: replace(), aslist(), astuple(), and iterator for dict(this).
        These methods won't override existing ones. They will be added only if the names aren't used.
      - Setting the default as ``None`` automatically makes the type into ``Optional``, if it isn't already.
      - Members without a default are allowed after members with a default
        (but they are required in order to create the instance)

    3. Misc
      - Frozen by default

    All of the above differences are configurable and extendable.


    Parameters:
        check_types (Union[bool, str]): Whether or not to validate the values, according to the given type annotations.
            Possible values: False, True, or 'cast'
        config (Configuration): Configuration to modify dataclass behavior, mostly regarding type validation.

    Example:
        ::

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

    # Get parent frame, to resolve forward-references
    _current_frame = inspect.currentframe()
    context_frame = _current_frame and _current_frame.f_back

    def wrap(cls):
        return _process_class(cls, config, check_types, context_frame,
                              init=init, repr=repr, eq=eq, order=order,
                              unsafe_hash=unsafe_hash, frozen=frozen, slots=slots)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)
