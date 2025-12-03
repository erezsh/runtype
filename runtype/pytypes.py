"""
Python Types - contains an implementation of a Runtype type system that is parallel to the Python type system.
"""

import io
import typing as t
import contextvars
import types
from abc import abstractmethod, ABC
from contextlib import suppress
import collections
from collections import abc
import sys
import typing
from datetime import datetime, date, time, timedelta
from types import FrameType

from .base_types import DataType, Validator, TypeMismatchError, dp, Variance
from . import base_types
from . import datetime_parse


try:
    import typing_extensions
except ImportError:
    typing_extensions = None



class LengthMismatchError(TypeMismatchError):
    pass

class CastFailed(TypeMismatchError):
    pass


class PythonType(base_types.Type, Validator):
    def cast_from(self, obj):
        raise NotImplementedError()


class Constraint(base_types.Constraint):
    def __init__(self, for_type, predicates):
        super().__init__(type_caster.to_canon(for_type), predicates)

    def cast_from(self, obj):
        obj = self.type.cast_from(obj)

        for p in self.predicates:
            if not p(obj):
                raise TypeMismatchError(obj, self)

        return obj



class AnyType(base_types.AnyType, PythonType):
    def test_instance(self, obj, sampler=None):
        return True

    def cast_from(self, obj):
        return obj

class AllType(base_types.AllType, PythonType):
    def test_instance(self, obj, sampler=None):
        return True

    def cast_from(self, obj):
        return obj

Any = AnyType()
All = AllType()


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
    
    def test_instance(self, obj, sampler=None):
        if not isinstance(obj, tuple):
            return False
        if self.types and len(obj) != len(self.types):
            return False
        for type_, item in zip(self.types, obj):
            if not type_.test_instance(item, sampler):
                return False
        return True


class SumType(base_types.SumType, PythonType):
    def __init__(self, types: typing.Sequence[PythonType]):
        # Here we merge all the instances of OneOf into a single one (if necessary).
        # The alternative is to turn all OneOf instances into SumTypes of single values.
        # I chose this method due to intuition that it's faster for the common use-case.
        one_ofs: typing.List[OneOf] = [t for t in types if isinstance(t, OneOf)]
        if len(one_ofs) > 1:
            rest = [t for t in types if not isinstance(t, OneOf)]
            types = rest + [OneOf([v for t in one_ofs for v in t.values])]
        super().__init__(types)

        # Optimization for instance validation
        data_types = []
        self.other_types = []
        for t in types:
            if isinstance(t, PythonDataType):
                data_types.append(t.kernel)
            else:
                self.other_types.append(t)
        self.data_types = tuple(data_types)
                

    def validate_instance(self, obj, sampler=None):
        if isinstance(obj, self.data_types):
            return
        for t in self.other_types:
            if t.test_instance(obj):
                return 
        raise TypeMismatchError(obj, self)

    def test_instance(self, obj, sampler=None):
        if isinstance(obj, self.data_types):
            return True
        for t in self.other_types:
            if t.test_instance(obj):
                return True
        return False

    def cast_from(self, obj):
        for t in self.types:
            with suppress(TypeError):
               return t.cast_from(obj)

        raise TypeMismatchError(obj, self)


# def _flatten_types(t):
#     if isinstance(t, SumType):
#         for t in t.types:
#             yield from _flatten_types(t)
#     else:
#         yield t



class PythonDataType(DataType, PythonType):
    kernel: type

    def __init__(self, kernel, supertypes={Any}):
        self.kernel = kernel

    def test_instance(self, obj, sampler=None):
        return isinstance(obj, self.kernel)

    def __repr__(self):
        try:
            return str(self.kernel.__name__)
        except AttributeError:      # Not a built-in type
            return repr(self.kernel)

    def cast_from(self, obj):
        if isinstance(obj, dict):
            # kernel is probably a class. Cast the dict into the class.
            return self.kernel(**obj)

        if not self.test_instance(obj):
            cast = getattr(self.kernel, 'cast_from', None)
            if cast:
                return cast(obj)
            raise

        return obj

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.kernel == other.kernel

    def __hash__(self):
        return hash((type(self), self.kernel))


class TupleType(PythonType):
    def test_instance(self, obj, sampler=None):
        return isinstance(obj, tuple)


# cv_type_checking allows the user to define different behaviors for their objects
# while they are being type-checked.
# This is especially useful if they overrode __hash__ or __eq__ in nonconventional ways.
cv_type_checking = contextvars.ContextVar('type_checking', default=False)


class OneOf(PythonType):
    values: typing.Sequence

    ALLOW_DISPATCH = False

    def __init__(self, values):
        self.values = values

    def test_instance(self, obj, sampler=None):
        tok = cv_type_checking.set(True)
        try:
            return obj in self.values
        finally:
            cv_type_checking.reset(tok)

    def __repr__(self):
        return 'Literal[%s]' % ', '.join(map(repr, self.values))

    def cast_from(self, obj):
        if obj not in self.values:
            raise TypeMismatchError(obj, self)

    def __hash__(self):
        return hash((type(self), frozenset(self.values)))



class GenericType(base_types.GenericType, PythonType):
    base: PythonDataType
    item: PythonType

    def __init__(self, base: PythonType, item: PythonType=Any, variance: Variance = Variance.Covariant):
        return super().__init__(base, item, variance)

class GenericContainerType(GenericType):
    def validate_instance(self, obj, sampler=None):
        self.base.validate_instance(obj)
        if not self.accepts_any:
            self.validate_instance_items(obj, sampler)

    def test_instance(self, obj, sampler=None):
        if not self.base.test_instance(obj):
            return False
        return self.accepts_any or self.test_instance_items(obj, sampler)

    def cast_from(self, obj):
        # Optimize for X[Any] and empty containers
        if not obj or self.accepts_any:
            # Make sure it's the right type
            return obj if self.base.test_instance(obj) else self.base.kernel(obj)

        return self.cast_from_items(obj)

    @property
    @abstractmethod
    def accepts_any(self) -> bool:
        ...

    @abstractmethod
    def validate_instance_items(self, items: t.Iterable, sampler):
        ...

    @abstractmethod
    def test_instance_items(self, items: t.Iterable, sampler) -> bool:
        ...

    @abstractmethod
    def cast_from_items(self, obj):
        ...

class SequenceType(GenericContainerType):
    @property
    def accepts_any(self):
        return self.item is Any

    def validate_instance_items(self, obj: t.Sequence, sampler):
        for item in sampler(obj) if sampler else obj:
            self.item.validate_instance(item, sampler)

    def test_instance_items(self, obj: t.Sequence, sampler) -> bool:
        return all(
            self.item.test_instance(item, sampler)
            for item in (sampler(obj) if sampler else obj)
        )

    def cast_from_items(self, obj: t.Sequence):
        # Recursively cast each item
        return self.base.kernel(self.item.cast_from(item) for item in obj)


class DictType(GenericContainerType):
    item: ProductType

    def __init__(self, base: PythonType, item=Any*Any, variance: Variance = Variance.Covariant):
        super().__init__(base, variance=variance)
        if isinstance(item, tuple):
            assert len(item) == 2
            item = ProductType([type_caster.to_canon(x) for x in item])
        self.item = item

    @property
    def accepts_any(self):
        return self.item is Any or self.item == Any*Any

    def validate_instance_items(self, obj: t.Mapping, sampler):
        assert isinstance(self.item, base_types.ProductType)
        kt, vt = self.item.types
        for k, v in sampler(obj.items()) if sampler else obj.items():
            try:
                kt.validate_instance(k, sampler)
                vt.validate_instance(v, sampler)
            except TypeMismatchError as e:
                raise TypeMismatchError((k, v), self.item) from e

    def test_instance_items(self, obj: t.Mapping, sampler) -> bool:
        assert isinstance(self.item, base_types.ProductType)
        kt, vt = self.item.types
        return all(
            kt.test_instance(k, sampler) and vt.test_instance(v, sampler)
            for k, v in (sampler(obj.items()) if sampler else obj.items())
        )

    def __getitem__(self, item):
        assert self.item == Any*Any
        return type(self)(self.base, item, self.variance)

    def cast_from_items(self, obj: t.Mapping):
        # Must already be a dict
        self.base.validate_instance(obj)

        # Recursively cast each item
        kt, vt = self.item.types
        return {kt.cast_from(k): vt.cast_from(v) for k, v in obj.items()}

class TupleEllipsisType(SequenceType):
    def __repr__(self):
        return '%s[%s, ...]' % (self.base, self.item)

class TypeType(GenericType):
    def test_instance(self, obj, sampler=None):
        t = type_caster.to_canon(obj)
        return t <= self.item

class CallableType(PythonDataType):
    args: PythonType = Any
    ret: PythonType = Any

    def __init__(self, args: PythonType = Any, ret: PythonType = Any):
        self.args = args
        self.ret = ret
        self.kernel = typing.Callable

    def __getitem__(self, signature):
        args, ret = signature
        return type(self)(args, ret)

    def __repr__(self):
        return f"Callable[{self.args}, {self.ret}]"


Object = PythonDataType(object)
Iter = SequenceType(PythonDataType(collections.abc.Iterable))
OrderedDict = DictType(PythonDataType(collections.OrderedDict), variance=Variance.Invariant)
Sequence = SequenceType(PythonDataType(abc.Sequence))
List = SequenceType(PythonDataType(list), variance=Variance.Invariant)
MutableSequence = SequenceType(PythonDataType(abc.MutableSequence), variance=Variance.Invariant)
Set = SequenceType(PythonDataType(set), variance=Variance.Invariant)
FrozenSet = SequenceType(PythonDataType(frozenset))
AbstractSet = SequenceType(PythonDataType(abc.Set))
Mapping = DictType(PythonDataType(abc.Mapping))
Dict = DictType(PythonDataType(dict), variance=Variance.Invariant)
MutableMapping = DictType(PythonDataType(abc.MutableMapping), variance=Variance.Invariant)
Tuple = TupleType()
TupleEllipsis = TupleEllipsisType(PythonDataType(tuple))
# Float = PythonDataType(float)
Bytes = PythonDataType(bytes)
Callable = CallableType()
Literal = OneOf
Type = TypeType(PythonDataType(type))

class _Bool(PythonDataType):
    pass

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
        if isinstance(obj, (int, str)):
            try:
                return float(obj)
            except ValueError:
                raise CastFailed()
        return super().cast_from(obj)

class _String(PythonDataType):
    def __call__(self, min_length=None, max_length=None):
        predicates = []
        if min_length is not None:
            predicates += [lambda s: len(s) >= min_length]
        if max_length is not None:
            predicates += [lambda s: len(s) <= max_length]

        if not predicates:
            return self

        return Constraint(self, predicates)



class _DateTime(PythonDataType):
    def cast_from(self, obj):
        if isinstance(obj, str):
            try:
                return datetime_parse.parse_datetime(obj)
            except datetime_parse.DateTimeError:
                raise TypeMismatchError(obj, self)
        return super().cast_from(obj)

class _Date(PythonDataType):
    def cast_from(self, obj):
        if isinstance(obj, str):
            try:
                return datetime_parse.parse_date(obj)
            except datetime_parse.DateTimeError:
                raise TypeMismatchError(obj, self)
        return super().cast_from(obj)

class _Time(PythonDataType):
    def cast_from(self, obj):
        if isinstance(obj, str):
            try:
                return datetime_parse.parse_time(obj)
            except datetime_parse.DateTimeError:
                raise TypeMismatchError(obj, self)
        return super().cast_from(obj)

class _TimeDelta(PythonDataType):
    def cast_from(self, obj):
        if isinstance(obj, str):
            try:
                return datetime_parse.parse_duration(obj)
            except datetime_parse.DateTimeError:
                raise TypeMismatchError(obj, self)
        return super().cast_from(obj)


class _NoneType(OneOf):
    ALLOW_DISPATCH = True   # Make an exception

    def __init__(self):
        super().__init__([None])

    def cast_from(self, obj):
        assert self.values == [None]
        if obj is not None:
            raise TypeMismatchError(obj, self)
        return None


String = _String(str)
Bool = _Bool(bool)
Int = _Int(int)
Float = _Float(float)
NoneType =  _NoneType()
DateTime = _DateTime(datetime)
Date = _Date(date)
Time = _Time(time)
TimeDelta = _TimeDelta(timedelta)


_type_cast_mapping = {
    iter: Iter,
    list: List,
    set: Set,
    frozenset: FrozenSet,
    dict: Dict,
    collections.OrderedDict: OrderedDict,
    tuple: Tuple,
    bool: Bool,
    None: NoneType,
    int: Int,
    str: String,
    float: Float,
    bytes: Bytes,
    type(None): NoneType,
    object: All,
    typing.Any: Any,
    datetime: DateTime,
    date: Date,
    time: Time,
    timedelta: TimeDelta,
}


class ATypeCaster(ABC):
    @abstractmethod
    def to_canon(self, t: typing.Any): ...


class TypeCaster(ATypeCaster):
    def __init__(self, frame: typing.Optional[FrameType]=None):
        self.cache: typing.Dict[typing.Union[type, PythonType], PythonType] = {}
        self.frame = frame

    def _to_canon(self, t):
        to_canon = self.to_canon

        if isinstance(t, (base_types.Type, Validator)):
            return t

        if isinstance(t, typing.ForwardRef):
            if self.frame is None:
                raise RuntimeError("Cannot resolve ForwardRef: TypeCaster initialized without a frame")
            t = typing._eval_type(t, self.frame.f_globals, self.frame.f_locals)

        if isinstance(t, tuple):
            return SumType.create([to_canon(x) for x in t])

        if hasattr(types, 'UnionType') and isinstance(t, types.UnionType):
            res = [to_canon(x) for x in t.__args__]
            return SumType.create(res)

        origin = getattr(t, '__origin__', None)
        if hasattr(typing, '_AnnotatedAlias') and isinstance(t, typing._AnnotatedAlias):
            return to_canon(origin)

        if typing_extensions:
            if hasattr(typing_extensions, '_AnnotatedAlias') and isinstance(t, typing_extensions._AnnotatedAlias):
                return to_canon(origin)
            elif hasattr(typing_extensions, 'AnnotatedMeta') and isinstance(t, typing_extensions.AnnotatedMeta):
                # Python 3.6
                return to_canon(t.__args__[0])

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
        elif t is typing.Mapping:
            return Mapping
        elif t is typing.MutableMapping:
            return MutableMapping
        elif t is typing.Sequence:
            return Sequence
        elif t is typing.MutableSequence:
            return MutableSequence
        elif t is typing.Callable:
            return Callable
        elif t is typing.IO:
            return PythonDataType(io.IOBase)
        elif t is typing.TextIO:
            return PythonDataType(io.TextIOBase)
        elif t is typing.BinaryIO:
            return PythonDataType(io.BytesIO)

        if origin is None:
            if isinstance(t, typing.TypeVar):
                return Any  # XXX is this correct?

            return PythonDataType(t)

        args = getattr(t, '__args__', None)

        if origin is list:
            x ,= args
            return List[to_canon(x)]
        elif origin is set:
            x ,= args
            return Set[to_canon(x)]
        elif origin is frozenset:
            x ,= args
            return FrozenSet[to_canon(x)]
        elif origin is dict:
            k, v = args
            return Dict[to_canon(k), to_canon(v)]
        elif origin is tuple:
            if not args:
                return Tuple
            if Ellipsis in args:
                if len(args) != 2 or args[0] == Ellipsis:
                    raise ValueError("Tuple with '...' expected to be of the exact form: tuple[t, ...].")
                return TupleEllipsis[to_canon(args[0])]

            return ProductType([to_canon(x) for x in args])

        elif origin is typing.Union:
            res = [to_canon(x) for x in args]
            return SumType(res)
        elif origin is abc.Callable or origin is typing.Callable:
            return Callable[ProductType(to_canon(x) for x in args[:-1]), to_canon(args[-1])]
        elif origin is typing.Literal:
            return OneOf(args)
        elif origin is abc.Mapping or origin is typing.Mapping:
            k, v = args
            return Mapping[to_canon(k), to_canon(v)]
        elif origin is abc.MutableMapping or origin is typing.MutableMapping:
            k, v = args
            return MutableMapping[to_canon(k), to_canon(v)]
        elif origin is abc.Sequence or origin is typing.Sequence:
            x ,= args
            return Sequence[to_canon(x)]
        elif origin is abc.Iterable or origin is typing.Iterable:
            x, = args
            return Iter[to_canon(x)]
        elif origin is abc.MutableSequence or origin is typing.MutableSequence:
            x ,= args
            return MutableSequence[to_canon(x)]
        elif origin is abc.MutableSet or origin is typing.MutableSet:
            x ,= args
            return Set[to_canon(x)]
        elif origin is abc.Set or origin is typing.AbstractSet:
            x ,= args
            return AbstractSet[to_canon(x)]
        elif origin is type or origin is typing.Type:
            if args:
                t ,= args
                return Type[self.to_canon(t)]
            # TODO test issubclass on t.__args__
            return Type
        elif origin is collections.OrderedDict:
            a, b = args
            return OrderedDict[to_canon(a), to_canon(b)]
        elif isinstance(t, typing._GenericAlias):
            return self._to_canon(origin)

        raise NotImplementedError("No support for type:", t)

    def to_canon(self, t) -> PythonType:
        try:
            return self.cache[t]
        except KeyError:
            try:
                res = _type_cast_mapping[t]
            except KeyError:
                res = self._to_canon(t)
            self.cache[t] = res     # memoize
            return res


type_caster = TypeCaster()


@dp
def le(self: PythonDataType, other: PythonDataType):
    return issubclass(self.kernel, other.kernel)
@dp
def le(self: CallableType, other: CallableType):
    return self.args >= other.args and self.ret <= other.ret
@dp
def le(self: TupleEllipsisType, other: TupleType):
    return True
@dp
def le(self: ProductType, other: TupleType):
    # Products are a tuple, but with length and specific types
    return True

@dp
def le(self: ProductType, other: TupleEllipsisType):
    return all(t <= other.item for t in self.types)

@dp
def le(self: PythonDataType, other: SequenceType):
    return self <= other.base and self <= other.item

@dp
def le(self: OneOf, other: OneOf):
    return set(self.values) <= set(other.values)

@dp
def le(self: OneOf, other: PythonType):
    try:
        for v in self.values:
            other.validate_instance(v)
    except TypeMismatchError:
        return False
    return True

@dp
def eq(self: PythonDataType, other: PythonDataType):
    return self.kernel == other.kernel

@dp
def eq(self: OneOf, other: OneOf):
    return self.values == other.values
