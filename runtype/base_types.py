"""
Base Type Classes - contains the basic building blocks of a generic type system
"""


class RuntypeError(TypeError):
    pass


class TypeMismatchError(RuntypeError):
    pass



class Type:
    """Abstract Type class. All types inherit from it.
    """
    def __add__(self, other):
        return SumType.create((self, other))

    def __mul__(self, other):
        return ProductType.create((self, other))


class AnyType(Type):
    """Represents the Any type.

    For any type 't' within the typesystem, t is a subset Any (or: t <= Any)
    """
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
    """Abstract class for a data type.

    Example of possible data-types: int, float, text
    """
    def __le__(self, other):
        if isinstance(other, DataType):
            return self == other

        return super().__le__(other)


class SumType(Type):
    """Implements a sum type, i.e. a disjoint union of a set of types.

    Similar to Python's Union.
    """
    def __init__(self, types):
        self.types = frozenset(types)

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
    """Implements a product type, i.e. a tuple of types.
    """

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
            return NotImplemented
        return self.types == other.types

    def __le__(self, other):
        if isinstance(other, ProductType):
            if len(self.types) != len(other.types):
                return False

            return all(t1<=t2 for t1, t2 in zip(self.types, other.types))
        elif isinstance(other, DataType):
            return False

        return NotImplemented


class ContainerType(DataType):
    """Base class for containers, such as generics.
    """
    def __getitem__(self, other):
        return GenericType(self, other)


class GenericType(ContainerType):
    """Implements a generic type. i.e. a container for items of a specific type.

    For any two generic types a[i] and b[j], it's true that a[i] <= b[j] iff a <= b and i <= j.
    """

    def __init__(self, base, item=Any):
        assert isinstance(item, (Type, type)), item
        if isinstance(base, GenericType):
            if not item <= base.item:
                raise TypeError(f"Expecting new generic to be a subtype of base, but {item} </= {base.item}")
            base = base.base

        self.base = base
        self.item = item

    def __repr__(self):
        if self.item is Any:
            return str(self.base)
        return '%r[%r]' % (self.base, self.item)

    def __getitem__(self, item):
        return type(self)(self, item)

    def __eq__(self, other):
        if isinstance(other, GenericType):
            return self.base == other.base and self.item == other.item
        elif isinstance(other, Type):
            return Any <= self.item and self.base == other
        return NotImplemented


    def __le__(self, other):
        if isinstance(other, GenericType):
            return self.base <= other.base and self.item <= other.item
        elif isinstance(other, DataType):
            return self.base <= other

        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, GenericType):
            return self.base >= other.base and self.item >= other.item
        elif isinstance(other, DataType):
            return self.base >= other

        return NotImplemented

    def __hash__(self):
        return hash((self.base, self.item))


class PhantomType(Type):
    """Implements a base for phantom types.
    """
    def __getitem__(self, other):
        return PhantomGenericType(self, other)

    def __le__(self, other):
        if isinstance(other, PhantomType):
            return self == other
        elif isinstance(other, PhantomGenericType):
            return NotImplemented
        return False

    def __ge__(self, other):
        if isinstance(other, PhantomType):
            return self == other
        elif isinstance(other, PhantomGenericType):
            return NotImplemented
        return False


class PhantomGenericType(GenericType):
    """Implements a generic phantom type, for carrying metadata within the type signature.

    For any phantom type p[i], it's true that p[i] <= p but also p[i] <= i and i <= p[i].
    """
    def __le__(self, other):
        if isinstance(other, PhantomType):
            return self.base <= other or self.item <= other
        elif isinstance(other, PhantomGenericType):
            return (self.base <= other.base and self.item <= other.item) or self.item <= other
        elif isinstance(other, DataType):
            return self.item <= other
        return NotImplemented

    def __eq__(self, other):
        return self.base == other and self.item == other

    def __ge__(self, other):
        if isinstance(other, PhantomType):
            return False
        elif isinstance(other, DataType):
            return other <= self.item
        return NotImplemented


class Validator:
    """Defines the validator interface.
    """
    def validate_instance(self, obj):
        raise NotImplementedError(self)

    def test_instance(self, obj):
        try:
            self.validate_instance(obj)
            return True
        except TypeMismatchError:
            return False

            
class Constraint(Validator, PhantomType):
    """Defines a constraint, which activates during validation.
    """

    def __init__(self, for_type, predicates):
        self.type = for_type
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
