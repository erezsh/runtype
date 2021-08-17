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
        except TypeMistmatchError as _e:
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

class TypeMistmatchError(RuntypeError):
    pass

class TupleLengthError(TypeMistmatchError):
    pass

class DataType(Type):
    def __init__(self, pytype, supertypes={Any}):
        self.pytype = pytype

    def __repr__(self):
        return self.pytype.__name__

    def __le__(self, other):
        if isinstance(other, DataType):
            return issubclass(self.pytype, other.pytype)

        return NotImplemented

    def validate_instance(self, obj):
        if not isinstance(obj, self.pytype):
            raise TypeMistmatchError(obj, self)

class OneOf(Type):
    def __init__(self, values):
        self.values = values

    def __le__(self, other):
        return NotImplemented

    def validate_instance(self, obj):
        if obj not in self.values:
            raise TypeMistmatchError(obj, self)

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
            raise TypeMistmatchError(obj, self)


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
            raise TypeMistmatchError(obj, self)

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
        if len(obj) != len(self.types):
            raise TupleLengthError(self, obj)
        for type_, item in zip(self.types, obj):
            type_.validate_instance(item)


class GenericType(DataType):
    def __init__(self, pytype, item=Any):
        super().__init__(pytype)
        assert isinstance(item, (Type, type)), item
        self.item = item

    def __repr__(self):
        return '%s[%s]' % (self.pytype.__name__, self.item)

    def __getitem__(self, item):
        assert self.item is Any, self.item
        return type(self)(self.pytype, item)

    def __eq__(self, other):
        if not isinstance(other, GenericType):
            return False
        return self.pytype == other.pytype and self.item == other.item

    def __le__(self, other):
        if isinstance(other, GenericType):
            return issubclass(self.pytype, other.pytype) and self.item <= other.item
        elif isinstance(other, DataType):
            return issubclass(self.pytype, other.pytype)
        elif isinstance(other, TupleType):
            return False    # tuples are generics, not the other way around

        return NotImplemented

    def __hash__(self):
        return hash((self.pytype, self.item))


class SequenceType(GenericType):

    def validate_instance(self, obj):
        if not isinstance(obj, self.pytype):
            raise TypeMistmatchError(obj, self)
        if self.item is not Any:
            for item in obj:
                self.item.validate_instance(item)

class DictType(GenericType):
    def __init__(self, pytype, item=Any*Any):
        super().__init__(pytype)
        if isinstance(item, tuple):
            assert len(item) == 2
            item = ProductType([cast_to_type(x) for x in item])
        self.item = item

    def validate_instance(self, obj):
        if not isinstance(obj, self.pytype):
            raise TypeMistmatchError(obj, self)
        if self.item is not Any:
            kt, vt = self.item.types
            for k, v in obj.items():
                kt.validate_instance(k)
                vt.validate_instance(v)

    def __getitem__(self, item):
        assert self.item == Any*Any
        return type(self)(self.pytype, item)



Object = DataType(object)
Iter = SequenceType(collections.Iterable)
List = SequenceType(list)
Set = SequenceType(set)
FrozenSet = SequenceType(frozenset)
Dict = DictType(dict)
Mapping = DictType(abc.Mapping)
Tuple = TupleType()
Int = DataType(int)
Str = DataType(str)
Float = DataType(float)
Bytes = DataType(bytes)
NoneType = DataType(type(None))
Callable = GenericType(abc.Callable)
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
        if t.__origin__ is origin_list:
            x ,= t.__args__
            return List[cast_to_type(x)]
        if t.__origin__ is origin_set:
            x ,= t.__args__
            return Set[cast_to_type(x)]
        if t.__origin__ is origin_frozenset:
            x ,= t.__args__
            return FrozenSet[cast_to_type(x)]
        if t.__origin__ is origin_dict:
            k, v = t.__args__
            return Dict[cast_to_type(k), cast_to_type(v)]
        if t.__origin__ is origin_tuple:
            return ProductType([cast_to_type(x) for x in t.__args__])
        if t.__origin__ is typing.Union:
            return SumType([cast_to_type(x) for x in t.__args__])
        if t.__origin__ is abc.Callable or t is typing.Callable:
            # return Callable[ProductType(cast_to_type(x) for x in t.__args__)]
            return Callable # TODO
        if py38 and t.__origin__ is typing.Literal:
            return OneOf(t.__args__)
        if t is typing.Mapping: # 3.6
            return Mapping
        elif t.__origin__ is abc.Mapping:
            k, v = t.__args__
            return Mapping[cast_to_type(k), cast_to_type(v)]

        raise NotImplementedError("No support for type:", t)

    if isinstance(t, typing.TypeVar):
        return Any  # XXX is this correct?

    return DataType(t)

def cast_to_type(t):
    try:
        return _type_cast_mapping[t]
    except KeyError:
        res = _cast_to_type(t)
        _type_cast_mapping[t] = res     # memoize
        return res

