"""
Python Types - contains an implementation of a Runtype type system that is parallel to the Python type system.
"""

from contextlib import suppress
import collections
from collections import abc
import sys
import typing
from datetime import datetime

from .base_types import DataType, Validator, TypeMismatchError
from . import base_types
from . import datetime_parse

py38 = sys.version_info >= (3, 8)


class LengthMismatchError(TypeMismatchError):
    pass


class PythonType(base_types.Type, Validator):
    pass



class Constraint(base_types.Constraint):
    def __init__(self, for_type, predicates):
        super().__init__(cast_to_type(for_type), predicates)

    def cast_from(self, obj):
        obj = self.type.cast_from(obj)

        for p in self.predicates:
            if not p(obj):
                raise TypeMismatchError(obj, self)

        return obj



class AnyType(base_types.AnyType, PythonType):
    def validate_instance(self, obj, sampler=None):
        return True

    def cast_from(self, obj):
        return obj


Any = AnyType()


class ProductType(base_types.ProductType, PythonType):
    """Used for Tuple
    """
    def validate_instance(self, obj, sampler=None):
        if not isinstance(obj, tuple):
            raise TypeMismatchError(obj, tuple)
        if self.types and len(obj) != len(self.types):
            raise LengthMismatchError(self, obj)
        for type_, item in zip(self.types, obj):
            type_.validate_instance(item, sampler)


class SumType(base_types.SumType, PythonType):
    def validate_instance(self, obj, sampler=None):
        if not any(t.test_instance(obj) for t in self.types):
            raise TypeMismatchError(obj, self)

    def cast_from(self, obj):
        for t in self.types:
            with suppress(TypeError):
               return t.cast_from(obj)

        raise TypeMismatchError(obj, self)


def _flatten_types(t):
    if isinstance(t, SumType):
        for t in t.types:
            yield from _flatten_types(t)
    else:
        yield t



class PythonDataType(DataType, PythonType):
    def __init__(self, kernel, supertypes={Any}):
        self.kernel = kernel

    def __le__(self, other):
        if isinstance(other, PythonDataType):
            return issubclass(self.kernel, other.kernel)

        return NotImplemented

    def validate_instance(self, obj, sampler=None):
        if not isinstance(obj, self.kernel):
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        try:
            return str(self.kernel.__name__)
        except AttributeError:      # Not a built-in type
            return repr(self.kernel)

    def cast_from(self, obj):
        if isinstance(obj, dict):
            # kernel is probably a class. Cast the dict into the class.
            return self.kernel(**obj)

        try:
            self.validate_instance(obj)
        except TypeMismatchError:
            cast = getattr(self.kernel, 'cast_from', None)
            if cast:
                return cast(obj)
            raise

        return obj


class TupleType(PythonType):
    def __le__(self, other):
        # No superclasses or subclasses
        if other is Any:
            return True

        return isinstance(other, TupleType)

    def __ge__(self, other):
        if isinstance(other, TupleType):
            return True
        elif isinstance(other, DataType):
            return False
        elif isinstance(other, ProductType):
            # Products are a tuple, but with length and types
            return True

        return NotImplemented

    def validate_instance(self, obj, sampler=None):
        if not isinstance(obj, tuple):
            raise TypeMismatchError(obj, self)


class OneOf(PythonType):
    def __init__(self, values):
        self.values = values

    def __le__(self, other):
        return NotImplemented

    def validate_instance(self, obj, sampler=None):
        if obj not in self.values:
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        return 'Literal[%s]' % ', '.join(map(repr, self.values))


class GenericType(base_types.GenericType, PythonType):
    def __init__(self, base, item=Any):
        return super().__init__(base, item)


class SequenceType(GenericType):

    def validate_instance(self, obj, sampler=None):
        self.base.validate_instance(obj)
        if self.item is not Any:
            if sampler:
                obj = sampler(obj)
            for item in obj:
                self.item.validate_instance(item, sampler)

    def cast_from(self, obj):
        # Optimize for List[Any] and empty sequences
        if self.item is Any or not obj:
            # Already a list?
            if self.base.test_instance(obj):
                return obj
            # Make sure it's a list
            return list(obj)

        # Recursively cast each item
        return [self.item.cast_from(item) for item in obj]


class DictType(GenericType):

    def __init__(self, base, item=Any*Any):
        super().__init__(base)
        if isinstance(item, tuple):
            assert len(item) == 2
            item = ProductType([cast_to_type(x) for x in item])
        self.item = item

    def validate_instance(self, obj, sampler=None):
        self.base.validate_instance(obj)
        if self.item is not Any:
            kt, vt = self.item.types
            items = obj.items()
            if sampler:
                items = sampler(items)
            for k, v in items:
                kt.validate_instance(k, sampler)
                vt.validate_instance(v, sampler)

    def __getitem__(self, item):
        assert self.item == Any*Any
        return type(self)(self.base, item)

    def cast_from(self, obj):
        # Must already be a dict
        self.base.validate_instance(obj)

        # Optimize for Dict[Any] and empty dicts
        if self.item is Any or not obj:
            return obj

        # Recursively cast each item
        kt, vt = self.item.types
        return {kt.cast_from(k): vt.cast_from(v) for k, v in obj.items()}


Object = PythonDataType(object)
Iter = SequenceType(PythonDataType(collections.abc.Iterable))
List = SequenceType(PythonDataType(list))
Sequence = SequenceType(PythonDataType(abc.Sequence))
Set = SequenceType(PythonDataType(set))
FrozenSet = SequenceType(PythonDataType(frozenset))
Dict = DictType(PythonDataType(dict))
Mapping = DictType(PythonDataType(abc.Mapping))
Tuple = TupleType()
TupleEllipsis = SequenceType(PythonDataType(tuple))
# Float = PythonDataType(float)
Bytes = PythonDataType(bytes)
Callable = PythonDataType(abc.Callable)  # TODO: Generic
Literal = OneOf


class _NoneType(PythonDataType):
    def cast_from(self, obj):
        if obj is not None:
            raise TypeMismatchError(obj, self)

class _Number(PythonDataType):
    def __call__(self, min=None, max=None):
        predicates = []
        if min is not None:
            predicates += [lambda i: i >= min]
        if max is not None:
            predicates += [lambda i: i <= max]

        return Constraint(self, predicates)

class _Int(_Number):
    def cast_from(self, obj):
        if isinstance(obj, str):
            return int(obj)
        return super().cast_from(obj)

class _Float(_Number):
    def cast_from(self, obj):
        if isinstance(obj, int):
            return float(obj)
        return super().cast_from(obj)

class _String(PythonDataType):
    def __call__(self, min_length=None, max_length=None):
        predicates = []
        if min_length is not None:
            predicates += [lambda s: len(s) >= min_length]
        if max_length is not None:
            predicates += [lambda s: len(s) <= max_length]

        return Constraint(self, predicates)


class _DateTime(PythonDataType):
    def cast_from(self, obj):
        if isinstance(obj, str):
            try:
                return datetime_parse.parse_datetime(obj)
            except datetime_parse.DateTimeError:
                raise TypeMismatchError(obj, self)
        return super().cast_from(obj)


String = _String(str)
Int = _Int(int)
Float = _Float(float)
NoneType = _NoneType(type(None))
DateTime = _DateTime(datetime)


_type_cast_mapping = {
    iter: Iter,
    list: List,
    set: Set,
    frozenset: FrozenSet,
    dict: Dict,
    tuple: Tuple,
    int: Int,
    str: String,
    float: Float,
    bytes: Bytes,
    type(None): NoneType,
    object: Any,
    typing.Any: Any,
    datetime: DateTime,

}


if sys.version_info >= (3, 7):
    origin_list = list
    origin_dict = dict
    origin_tuple = tuple
    origin_set = set
    origin_frozenset = frozenset
else:
    origin_list = typing.List
    origin_dict = typing.Dict
    origin_tuple = typing.Tuple
    origin_set = typing.Set
    origin_frozenset = typing.FrozenSet


def _cast_to_type(t):
    if isinstance(t, Validator):
        return t

    if isinstance(t, tuple):
        return SumType([cast_to_type(x) for x in t])

    try:
        t.__origin__
    except AttributeError:
        pass
    else:
        if getattr(t, '__args__', None) is None:
            if t is typing.List:
                return List
            elif t is typing.Dict:
                return Dict
            elif t is typing.Set:
                return Set
            elif t is typing.FrozenSet:
                return FrozenSet
            elif t is typing.Tuple:
                return Tuple
            elif t is typing.Mapping:  # 3.6
                return Mapping
            elif t is typing.Sequence:
                return Sequence

        if t.__origin__ is origin_list:
            x ,= t.__args__
            return List[cast_to_type(x)]
        elif t.__origin__ is origin_set:
            x ,= t.__args__
            return Set[cast_to_type(x)]
        elif t.__origin__ is origin_frozenset:
            x ,= t.__args__
            return FrozenSet[cast_to_type(x)]
        elif t.__origin__ is origin_dict:
            k, v = t.__args__
            return Dict[cast_to_type(k), cast_to_type(v)]
        elif t.__origin__ is origin_tuple:
            if Ellipsis in t.__args__:
                if len(t.__args__) != 2 or t.__args__[0] == Ellipsis:
                    raise ValueError("Tuple with '...'' expected to be of the exact form: tuple[t, ...].")
                return TupleEllipsis[cast_to_type(t.__args__[0])]

            return ProductType([cast_to_type(x) for x in t.__args__])

        elif t.__origin__ is typing.Union:
            return SumType([cast_to_type(x) for x in t.__args__])
        elif t.__origin__ is abc.Callable or t is typing.Callable:
            # return Callable[ProductType(cast_to_type(x) for x in t.__args__)]
            return Callable  # TODO
        elif py38 and t.__origin__ is typing.Literal:
            return OneOf(t.__args__)
        elif t.__origin__ is abc.Mapping or t.__origin__ is typing.Mapping:
            k, v = t.__args__
            return Mapping[cast_to_type(k), cast_to_type(v)]
        elif t.__origin__ is abc.Sequence or t.__origin__ is typing.Sequence:
            x ,= t.__args__
            return Sequence[_cast_to_type(x)]

        elif t.__origin__ is type or t.__origin__ is typing.Type:
            # TODO test issubclass on t.__args__
            return PythonDataType(type)

        raise NotImplementedError("No support for type:", t)

    if isinstance(t, typing.TypeVar):
        return Any  # XXX is this correct?

    return PythonDataType(t)


def cast_to_type(t):
    try:
        return _type_cast_mapping[t]
    except KeyError:
        res = _cast_to_type(t)
        _type_cast_mapping[t] = res     # memoize
        return res

