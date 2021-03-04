from collections import abc
import typing

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

Any = AnyType()

def _get_supertypes(t):
    yield t
    for st in t.supertypes:
        yield from _get_supertypes(st)

class RuntypeError(TypeError):
    pass

class TypeMistmatchError(RuntypeError):
    pass

class TupleLengthError(TypeMistmatchError):
    pass

class DataType(Type):
    def __init__(self, pytype, supertypes={Any}):
        self.pytype = pytype
        self.supertypes = frozenset(supertypes)

    def __repr__(self):
        return self.pytype.__name__

    def __le__(self, other):
        if isinstance(other, DataType):
            return self in _get_supertypes(other)

        return NotImplemented

    def validate_instance(self, obj):
        if not isinstance(obj, self.pytype):
            raise TypeMistmatchError(self, obj)

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
        if not isinstance(other, SumType):
            return False

        return any(other <= t for t in self.types)

    def __eq__(self, other):
        if not isinstance(other, SumType):
            return False
        return self.types == other.types

    def __hash__(self):
        return hash(frozenset(self.types))

    def validate_instance(self, obj):
        if not any(t.test_instance(obj) for t in self.types):
            raise TypeMistmatchError(self, obj)


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
        if isinstance(other, ProductType):
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


Any = AnyType()


class GenericType(DataType):
    def __init__(self, pytype, item=Any):
        super().__init__(pytype)
        assert isinstance(item, (Type, type)), item
        self.item = item

    def __repr__(self):
        return '%s[%s]' % (self.pytype.__name__, self.item)

    def __getitem__(self, item):
        assert self.item is Any
        return type(self)(self.pytype, item)

    def __eq__(self, other):
        if not isinstance(other, GenericType):
            return False
        return self.pytype == other.pytype and self.item == other.item

    def __le__(self, other):
        if isinstance(other, GenericType):
            return issubclass(self.pytype, other.pytype) and self.item <= other.item

        return NotImplemented

    def __hash__(self):
        return hash((self.pytype, self.item))


class SequenceType(GenericType):
    def validate_instance(self, obj):
        if not isinstance(obj, self.pytype):
            raise TypeMistmatchError(self, obj)
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
            raise TypeMistmatchError(self, obj)
        if self.item is not Any:
            kt, vt = self.item.types
            for k, v in obj.items():
                kt.validate_instance(k)
                vt.validate_instance(v)

    def __getitem__(self, item):
        assert self.item == Any*Any
        return type(self)(self.pytype, item)


Object = DataType(object)
List = SequenceType(list)
Set = SequenceType(set)
Dict = DictType(dict)
Tuple = GenericType(tuple)
Int = DataType(int)
Str = DataType(str)
Float = DataType(float)
Bytes = DataType(bytes)
NoneType = DataType(type(None))
Callable = GenericType(abc.Callable)


_type_cast_mapping = {
    list: List,
    set: Set,
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
        if t.__origin__ is list:
            x ,= t.__args__
            return List[cast_to_type(x)]
        if t.__origin__ is dict:
            k, v = t.__args__
            return Dict[cast_to_type(k), cast_to_type(v)]
        if t.__origin__ is tuple:
            return ProductType([cast_to_type(x) for x in t.__args__])
        if t.__origin__ is typing.Union:
            return SumType([cast_to_type(x) for x in t.__args__])
        if t.__origin__ is abc.Callable:
            # return Callable[ProductType(cast_to_type(x) for x in t.__args__)]
            return Callable # TODO

        assert False, t

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


def ensure_isa(obj, t):
    t = cast_to_type(t)
    t.validate_instance(obj)
