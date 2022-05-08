"""
Base Type Classes - contains the basic building blocks of a generic type system

We use comparison operators to indicate whether a type is a subtype of another:
 - t1 <= t2 means "t1 is a subtype of t2"
 - t1 >= t2 means "t2 is a subtype of t1"
This is consistent with the view that a type hierarchy can be expressed as a poset.
"""
from typing import Callable, Sequence, Optional
from abc import ABC, abstractmethod


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

    For any type 't' within the typesystem, t is a subtype of Any (or: t <= Any)
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

    Similar to Python's `typing.Union`.
    """
    def __init__(self, types):
        self.types = frozenset(types)

    @classmethod
    def create(cls, types):
        x = set()
        for t in types:
            if isinstance(t, SumType):
                # Optimization: Flatten recursive SumTypes
                x |= set(t.types)
            else:
                x.add(t)

        if len(x) == 1:         # SumType([x]) is x
            return list(x)[0]
        return cls(x)

    def __repr__(self):
        return '(%s)' % '+'.join(map(repr, self.types))

    def __le__(self, other):
        return all(t <= other for t in self.types)

    def __ge__(self, other):
        return any(other <= t for t in self.types)

    def __eq__(self, other):
        if isinstance(other, SumType):
            return self.types == other.types

        return NotImplemented

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
                # Flatten recursive ProductTypes, so that a*b*c == (a,b,c), instead of ((a,b), c)
                x += t.types
            else:
                x.append(t)

        return cls(x)

    def __repr__(self):
        return '(%s)' % '*'.join(map(repr, self.types))

    def __hash__(self):
        return hash(self.types)

    def __eq__(self, other):
        if isinstance(other, ProductType):
            return self.types == other.types

        return NotImplemented

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

        elif not isinstance(other, PhantomGenericType):
            return False

        return NotImplemented


    def __ge__(self, other):
        if isinstance(other, PhantomType):
            return self == other

        elif not isinstance(other, PhantomGenericType):
            return False

        return NotImplemented


class PhantomGenericType(Type):
    """Implements a generic phantom type, for carrying metadata within the type signature.

    For any phantom type p[i], it's true that p[i] <= p but also p[i] <= i and i <= p[i].
    """
    def __init__(self, base, item=Any):
        self.base = base
        self.item = item

    def __le__(self, other):
        if isinstance(other, PhantomType):
            return self.base <= other or self.item <= other

        elif isinstance(other, PhantomGenericType):
            return (self.base <= other.base and self.item <= other.item) or self.item <= other

        elif isinstance(other, DataType):
            return self.item <= other

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, PhantomGenericType):
            return self.base == other.base and self.item == other.base

        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, PhantomType):
            return False

        elif isinstance(other, DataType):
            return other <= self.item

        return NotImplemented

SamplerType = Callable[[Sequence], Sequence]

class Validator(ABC):
    """Defines the validator interface.
    """
    @abstractmethod
    def validate_instance(self, obj, sampler: Optional[SamplerType]=None):
        """Validates obj, raising a TypeMismatchError if it does not conform.

        If sampler is provided, it will be applied to the instance in order to 
        validate only a sample of the object. This approach may validate much faster,
        but might miss anomalies in the data.
        """
        ...


    def test_instance(self, obj, sampler=None):
        """Tests obj, returning a True/False for whether it conforms or not.

        If sampler is provided, it will be applied to the instance in order to 
        validate only a sample of the object.
        """
        try:
            self.validate_instance(obj, sampler)
            return True
        except TypeMismatchError:
            return False

            
class Constraint(Validator, PhantomType):
    """Defines a constraint, which activates during validation.
    """

    def __init__(self, for_type, predicates):
        self.type = for_type
        self.predicates = predicates

    def validate_instance(self, inst, sampler=None):
        """Makes sure the instance conforms by applying it to all the predicates."""
        self.type.validate_instance(inst, sampler)

        for p in self.predicates:
            if not p(inst):
                raise TypeMismatchError(inst, self)

    def __ge__(self, other):
        # Arbitrary predicates prevent it from being a superclass
        return False

    def __le__(self, other):
        return self.type <= other
