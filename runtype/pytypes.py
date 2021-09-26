"""
Python Types - contains an implementation of a Runtype type system that is parallel to the Python type system.
"""

from contextlib import suppress
import collections
from collections import abc
import sys
import typing
from datetime import datetime

from .base_types import AnyType, DataType, GenericType, ProductType, SumType, Type, PhantomType

py38 = sys.version_info >= (3, 8)


class RuntypeError(TypeError):
    pass


class TypeMismatchError(RuntypeError):
    pass


class LengthMismatchError(TypeMismatchError):
    pass


class Validator:
    def validate_instance(self, obj):
        raise NotImplementedError(self)

    def test_instance(self, obj):
        try:
            self.validate_instance(obj)
            return True
        except TypeMismatchError as _e:
            return False


class PythonType(Type, Validator):
    pass


class Constraint(Validator, PhantomType):
    def __init__(self, for_type, predicates):
        self.type = cast_to_type(for_type)
        self.predicates = predicates

    def validate_instance(self, inst):
        self.type.validate_instance(inst)

        for p in self.predicates:
            if not p(inst):
                raise TypeMismatchError(inst, self)

    def __ge__(self, other):
        return self.type >= other
    def __le__(self, other):
        return self.type <= other

    def cast_from(self, obj):
        obj = self.type.cast_from(obj)

        for p in self.predicates:
            if not p(obj):
                raise TypeMismatchError(obj, self)

        return obj




class AnyType(AnyType, PythonType):
    def validate_instance(self, obj):
        return True

    def cast_from(self, obj):
        return obj


Any = AnyType()


class ProductType(ProductType, PythonType):
    def validate_instance(self, obj):
        if self.types and len(obj) != len(self.types):
            raise LengthMismatchError(self, obj)
        for type_, item in zip(self.types, obj):
            type_.validate_instance(item)


class SumType(SumType, PythonType):
    def validate_instance(self, obj):
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
    def __init__(self, kernel: type, supertypes={Any}):
        self.kernel = kernel

    def __le__(self, other):
        if isinstance(other, PythonDataType):
            return issubclass(self.kernel, other.kernel)

        return NotImplemented

    def validate_instance(self, obj):
        if not isinstance(obj, self.kernel):
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        return str(self.kernel.__name__)

    def cast_from(self, obj):
        if isinstance(obj, dict):
            # kernel is probably a class. Cast the dict into the class.
            return self.kernel(**obj)

        self.validate_instance(obj)
        return obj


class TupleType(PythonType):
    def __le__(self, other):
        # No superclasses or subclasses
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

    def validate_instance(self, obj):
        if not isinstance(obj, tuple):
                raise TypeMismatchError(obj, self)


class OneOf(PythonType):
    def __init__(self, values):
        self.values = values

    def __le__(self, other):
        return NotImplemented

    def validate_instance(self, obj):
        if obj not in self.values:
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        return 'Literal[%s]' % ', '.join(map(repr, self.values))


class GenericType(GenericType, PythonType):
    def __init__(self, base, item=Any):
        return super().__init__(base, item)


class SequenceType(GenericType):

    def validate_instance(self, obj):
        self.base.validate_instance(obj)
        if self.item is not Any:
            for item in obj:
                self.item.validate_instance(item)

    def cast_from(self, obj):
        if self.item is Any or not obj:
            if self.base.test_instance(obj):
                return obj
            return list(obj)
        return [self.item.cast_from(item) for item in obj]


class DictType(GenericType):

    def __init__(self, base, item=Any*Any):
        super().__init__(base)
        if isinstance(item, tuple):
            assert len(item) == 2
            item = ProductType([cast_to_type(x) for x in item])
        self.item = item

    def validate_instance(self, obj):
        self.base.validate_instance(obj)
        if self.item is not Any:
            kt, vt = self.item.types
            for k, v in obj.items():
                kt.validate_instance(k)
                vt.validate_instance(v)

    def __getitem__(self, item):
        assert self.item == Any*Any
        return type(self)(self.base, item)

    def cast_from(self, obj):
        self.base.validate_instance(obj)
        if self.item is Any or not obj:
            return obj

        kt, vt = self.item.types
        return {kt.cast_from(k): vt.cast_from(v) for k, v in obj.items()}


Object = PythonDataType(object)
Iter = SequenceType(collections.abc.Iterable)
List = SequenceType(PythonDataType(list))
Set = SequenceType(PythonDataType(set))
FrozenSet = SequenceType(PythonDataType(frozenset))
Dict = DictType(PythonDataType(dict))
Mapping = DictType(PythonDataType(abc.Mapping))
Tuple = TupleType()
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


from . import datetime_parse

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
            return ProductType([cast_to_type(x) for x in t.__args__])

        elif t.__origin__ is typing.Union:
            return SumType([cast_to_type(x) for x in t.__args__])
        elif t.__origin__ is abc.Callable or t is typing.Callable:
            # return Callable[ProductType(cast_to_type(x) for x in t.__args__)]
            return Callable  # TODO
        elif py38 and t.__origin__ is typing.Literal:
            return OneOf(t.__args__)
        elif t.__origin__ is abc.Mapping:
            k, v = t.__args__
            return Mapping[cast_to_type(k), cast_to_type(v)]

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

