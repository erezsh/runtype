import sys
import collections
from collections import abc
import typing

py38 = sys.version_info >= (3,8)

class Type:
    def __add__(self, other):
        return SumType.create((self, other))
    def __mul__(self, other):
        return ProductType((self, other))

    def validate_instance(self, obj):
        raise NotImplementedError(self)

    def test_instance(self, obj):
        try:
            self.validate_instance(obj)
            return True
        except TypeMismatchError as _e:
            return False

class AnyType(Type):
    supertypes = ()

    def __add__(self, other):
        return self

    def __ge__(self, other):
        if isinstance(other, (type, Type)):
            return True

        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Type):
            return other is self

        return NotImplemented

    def validate_instance(self, obj):
        return True

    def __repr__(self):
        return 'Any'


Any = AnyType()


class RuntypeError(TypeError):
    pass

class TypeMismatchError(RuntypeError):
    pass

class TupleLengthError(TypeMismatchError):
    pass

class DataType(Type):
    def __init__(self, kernel, supertypes={Any}):
        self.kernel = kernel

    def __repr__(self):
        return str(self.kernel)  #.__name__

class PythonDataType(DataType):
    def __le__(self, other):
        if isinstance(other, PythonDataType):
            return issubclass(self.kernel, other.kernel)

        return NotImplemented

    def validate_instance(self, obj):
        if not isinstance(obj, self.kernel):
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        return str(self.kernel.__name__)

class OneOf(Type):
    def __init__(self, values):
        self.values = values

    def __le__(self, other):
        return NotImplemented

    def validate_instance(self, obj):
        if obj not in self.values:
            raise TypeMismatchError(obj, self)

    def __repr__(self):
        return 'Literal[%s]' % ', '.join(map(repr, self.values))


class SumType(Type):
    def __init__(self, types):
        self.types = set(types)

    @classmethod
    def create(cls, types):
        x = set()
        for t in types:
            if isinstance(t, SumType):
                x |= set(t.types)
            else:
                x.add(t)

        if len(x) == 1:
            return list(x)[0]
        return cls(x)

    def __repr__(self):
        return '(%s)' % '+'.join(map(repr, self.types))

    def __le__(self, other):
        return all(t <= other for t in self.types)

    def __ge__(self, other):
        if not isinstance(other, Type):
            return NotImplemented

        return any(other <= t for t in self.types)

    def __eq__(self, other):
        if not isinstance(other, SumType):
            return NotImplemented
        return self.types == other.types

    def __hash__(self):
        return hash(frozenset(self.types))

    def validate_instance(self, obj):
        if not any(t.test_instance(obj) for t in self.types):
            raise TypeMismatchError(obj, self)


class TupleType(Type):
    def __le__(self, other):
        # No superclasses or subclasses
        return isinstance(other, TupleType)

    def __ge__(self, other):
        if isinstance(other, TupleType):
            return True
        elif isinstance(other, DataType):
            return False

        return NotImplemented

    def validate_instance(self, obj):
        if not isinstance(obj, tuple):
            raise TypeMismatchError(obj, self)

class ProductType(Type):
    def __init__(self, types):
        self.types = tuple(types)

    def __repr__(self):
        return '(%s)' % '*'.join(map(repr, self.types))

    def __hash__(self):
        return hash(self.types)

    def __eq__(self, other):
        if not isinstance(other, ProductType):
            return False
        return self.types == other.types

    def __le__(self, other):
        if isinstance(other, TupleType):
            # Products are a tuple, but with length and types
            return True
        elif isinstance(other, ProductType):
            if len(self.types) != len(other.types):
                return False

            return all(t1<=t2 for t1, t2 in zip(self.types, other.types))
        elif isinstance(other, DataType):
            return False

        return NotImplemented

    def validate_instance(self, obj):
        if self.types and len(obj) != len(self.types):
            raise TupleLengthError(self, obj)
        for type_, item in zip(self.types, obj):
            type_.validate_instance(item)


class GenericType(Type):
    def __init__(self, base, item=Any):
        assert isinstance(item, (Type, type)), item
        self.base = base
        self.item = item

    def __repr__(self):
        return '%r[%r]' % (self.base, self.item)

    def __getitem__(self, item):
        assert self.item is Any, self.item
        return type(self)(self.base, item)

    def __eq__(self, other):
        if not isinstance(other, GenericType):
            return False
        return self.base == other.base and self.item == other.item

    def __le__(self, other):
        if isinstance(other, GenericType):
            return self.base <= other.base and self.item <= other.item
        elif isinstance(other, DataType):
            return self.base <= other
        elif isinstance(other, TupleType):
            return False    # tuples are generics, not the other way around

        return NotImplemented

    def __ge__(self, other):
        return not self <= other

    def __hash__(self):
        return hash((self.base, self.item))

    def validate_instance(self, obj):
        raise NotImplementedError()


class SequenceType(GenericType):

    def validate_instance(self, obj):
        self.base.validate_instance(obj)
        if self.item is not Any:
            for item in obj:
                self.item.validate_instance(item)

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



Object = PythonDataType(object)
Iter = SequenceType(collections.abc.Iterable)
List = SequenceType(PythonDataType(list))
Set = SequenceType(PythonDataType(set))
FrozenSet = SequenceType(PythonDataType(frozenset))
Dict = DictType(PythonDataType(dict))
Mapping = DictType(PythonDataType(abc.Mapping))
Tuple = TupleType()
Int = PythonDataType(int)
Str = PythonDataType(str)
Float = PythonDataType(float)
Bytes = PythonDataType(bytes)
NoneType = PythonDataType(type(None))
Callable = PythonDataType(abc.Callable) # TODO: Generic
Literal = OneOf


_type_cast_mapping = {
    iter: Iter,
    list: List,
    set: Set,
    frozenset: FrozenSet,
    dict: Dict,
    tuple: Tuple,
    int: Int,
    str: Str,
    float: Float,
    bytes: Bytes,
    type(None): NoneType,
    object: Any,
    typing.Any: Any,

}


if sys.version_info >= (3,7):
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
    if isinstance(t, Type):
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
            elif t is typing.Mapping: # 3.6
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
            return Callable # TODO
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

