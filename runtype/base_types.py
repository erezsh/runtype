"""
Base Types - contains the basic building blocks of a generic type system
"""

class RuntypeError(TypeError):
    pass

class TypeMismatchError(RuntypeError):
    pass


class Type:
    def __add__(self, other):
        return SumType.create((self, other))
    def __mul__(self, other):
        return ProductType.create((self, other))


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

    def __repr__(self):
        return 'Any'


Any = AnyType()


class DataType(Type):
    def __init__(self, kernel, supertypes={Any}):
        self.kernel = kernel

    def __repr__(self):
        return str(self.kernel)  #.__name__


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



class ProductType(Type):

    def __init__(self, types):
        self.types = tuple(types)

    @classmethod
    def create(cls, types):
        x = []
        for t in types:
            if isinstance(t, ProductType):
                x += t.types
            else:
                x.append(t)

        return cls(x)

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


class GenericType(Type):
    def __init__(self, base, item=Any):
        assert isinstance(item, (Type, type)), item
        self.base = base
        self.item = item

    def __repr__(self):
        return '%r[%r]' % (self.base, self.item)

    def __getitem__(self, item):
        assert isinstance(self.item, AnyType), self.item
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

        return NotImplemented

    def __ge__(self, other):
        return not self <= other

    def __hash__(self):
        return hash((self.base, self.item))

