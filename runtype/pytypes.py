"""
Python Types - contains an implementation of a Runtype type system that is parallel to the Python type system.
"""

from abc import abstractmethod, ABC
from contextlib import suppress
import collections
from collections import abc
import sys
import typing
from datetime import datetime, date, time, timedelta
from types import FrameType

from .utils import ForwardRef
from .base_types import DataType, Validator, TypeMismatchError
from . import base_types
from . import datetime_parse


if sys.version_info < (3, 9):
    if sys.version_info < (3, 7):
        # python 3.6 
        _orig_eval = ForwardRef._eval_type
    else:
        _orig_eval = ForwardRef._evaluate

    def _forwardref_evaluate(self, glob, loc, _):
        return _orig_eval(self, glob, loc)
else:
    _forwardref_evaluate = ForwardRef._evaluate

try:
    import typing_extensions
except ImportError:
    typing_extensions = None



py38 = sys.version_info >= (3, 8)


class LengthMismatchError(TypeMismatchError):
    pass

class CastFailed(TypeMismatchError):
    pass


class PythonType(base_types.Type, Validator):
    pass



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
    def __init__(self, types: typing.Sequence[PythonType]):
        # Here we merge all the instances of OneOf into a single one (if necessary).
        # The alternative is to turn all OneOf instances into SumTypes of single values.
        # I chose this method due to intuition that it's faster for the common use-case.
        one_ofs: typing.List[OneOf] = [t for t in types if isinstance(t, OneOf)]
        if len(one_ofs) > 1:
            rest = [t for t in types if not isinstance(t, OneOf)]
            types = rest + [OneOf([v for t in one_ofs for v in t.values])]
        super().__init__(types)

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
    values: typing.Sequence

    def __init__(self, values):
        self.values = values

    def __le__(self, other):
        if isinstance(other, OneOf):
            return set(self.values) <= set(other.values)
        elif isinstance(other, PythonType):
            try:
                for v in self.values:
                    other.validate_instance(v)
            except TypeMismatchError:
                return False
            return True
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, OneOf):
            return set(self.values) >= set(other.values)
        elif isinstance(other, PythonType):
            return False
        return NotImplemented

    def validate_instance(self, obj, sampler=None):
        if obj not in self.values:
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        return 'Literal[%s]' % ', '.join(map(repr, self.values))

    def cast_from(self, obj):
        if obj not in self.values:
            raise TypeMismatchError(obj, self)


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
            item = ProductType([type_caster.to_canon(x) for x in item])
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
    def __init__(self):
        super().__init__([None])

    def cast_from(self, obj):
        assert self.values == [None]
        if obj is not None:
            raise TypeMismatchError(obj, self)
        return None


String = _String(str)
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
    tuple: Tuple,
    int: Int,
    str: String,
    float: Float,
    bytes: Bytes,
    type(None): NoneType,
    object: Any,
    typing.Any: Any,
    datetime: DateTime,
    date: Date,
    time: Time,
    timedelta: TimeDelta,
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

        if isinstance(t, ForwardRef):
            if self.frame is None:
                raise RuntimeError("Cannot resolve ForwardRef: TypeCaster initialized without a frame")
            t = _forwardref_evaluate(t, self.frame.f_globals, self.frame.f_locals, frozenset())

        if isinstance(t, tuple):
            return SumType([to_canon(x) for x in t])

        if hasattr(typing, '_AnnotatedAlias') and isinstance(t, typing._AnnotatedAlias):
            return to_canon(t.__origin__)

        if typing_extensions:
            if hasattr(typing_extensions, '_AnnotatedAlias') and isinstance(t, typing_extensions._AnnotatedAlias):
                return to_canon(t.__origin__)
            elif hasattr(typing_extensions, 'AnnotatedMeta') and isinstance(t, typing_extensions.AnnotatedMeta):
                # Python 3.6
                return to_canon(t.__args__[0])

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
                return List[to_canon(x)]
            elif t.__origin__ is origin_set:
                x ,= t.__args__
                return Set[to_canon(x)]
            elif t.__origin__ is origin_frozenset:
                x ,= t.__args__
                return FrozenSet[to_canon(x)]
            elif t.__origin__ is origin_dict:
                k, v = t.__args__
                return Dict[to_canon(k), to_canon(v)]
            elif t.__origin__ is origin_tuple:
                if Ellipsis in t.__args__:
                    if len(t.__args__) != 2 or t.__args__[0] == Ellipsis:
                        raise ValueError("Tuple with '...'' expected to be of the exact form: tuple[t, ...].")
                    return TupleEllipsis[to_canon(t.__args__[0])]

                return ProductType([to_canon(x) for x in t.__args__])

            elif t.__origin__ is typing.Union:
                res = [to_canon(x) for x in t.__args__]
                return SumType(res)
            elif t.__origin__ is abc.Callable or t is typing.Callable:
                # return Callable[ProductType(to_canon(x) for x in t.__args__)]
                return Callable  # TODO
            elif py38 and t.__origin__ is typing.Literal:
                return OneOf(t.__args__)
            elif t.__origin__ is abc.Mapping or t.__origin__ is typing.Mapping:
                k, v = t.__args__
                return Mapping[to_canon(k), to_canon(v)]
            elif t.__origin__ is abc.Sequence or t.__origin__ is typing.Sequence:
                x ,= t.__args__
                return Sequence[to_canon(x)]
            elif t.__origin__ is type or t.__origin__ is typing.Type:
                # TODO test issubclass on t.__args__
                return PythonDataType(type)

            raise NotImplementedError("No support for type:", t)

        if isinstance(t, typing.TypeVar):
            return Any  # XXX is this correct?

        return PythonDataType(t)

    def to_canon(self, t):
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
