"""
Base Type Classes - contains the basic building blocks of a generic type system

There are six kinds of types: (to date)
- Any - May contain any type, or be contained by any type
- All - Contains all types
- Sum - marks a union between types
- Product - marks a record / tuple / struct
- Data - marks any type that contains non-type information
- Phantom - A "meta"-type that can wrap existing types,
            but is transparent, and has no effect otherwise.

We use comparison operators to indicate whether a type is a subtype of another:
 - t1 <= t2 means "t1 is a subtype of t2"
 - t1 >= t2 means "t2 is a subtype of t1"
This is consistent with the view that type hierarchies can be expressed as a posets.

A sum that contains All becomes All. Not so with Any.
"""
from typing import Callable, Sequence, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum, auto

from .dispatch import MultiDispatch
from .typesystem import PythonBasic

dp = MultiDispatch(PythonBasic())


class RuntypeError(TypeError):
    pass


class TypeMismatchError(RuntypeError):
    def __str__(self) -> str:
        v, t = self.args
        return f"Expected type '{t}', but got value: {v}."


_Type = Union["Type", type]


class Type(ABC):
    """Abstract Type class. Every type inherit from it."""

    def __add__(self, other: _Type):
        return SumType.create((self, other))

    def __mul__(self, other: _Type):
        return ProductType((self, other))

    def __le__(self, other):
        return NotImplemented

class AnyType(Type):
    """Represents the Any type.

    Any may contain any other type, and be contained by any other type.

    For any type 't' within the typesystem, t is a subtype of Any (or: t <= Any)
    But also Any is a subtype of t (or: Any <= t)
    """

    def __repr__(self):
        return "Any"


class AllType(Type):
    """Represents the All type.

    All contains every other type.

    For any type 't' within the typesystem, t is a subtype of All (or: t <= All)
    if All <= t, then t == All
    """

    def __add__(self, other):
        if not isinstance(other, (type, Type)):
            return NotImplemented
        return self

    __radd__ = __add__

    def __repr__(self):
        return "All"


Any = AnyType()
All = AllType()


class DataType(Type):
    """Abstract class for a data type.

    A data-type is any type that contains non-type information.

    Example of possible data-types: int, float, text, list
    """


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
            elif isinstance(t, AllType):
                # This is more than an optimization, as it allows users to say:
                # (All + x) is All
                return t
            else:
                x.add(t)

        if len(x) == 1:  # SumType([x]) is x
            return list(x)[0]
        return cls(x)

    def __repr__(self):
        return "(%s)" % "+".join(map(repr, self.types))

    def __hash__(self):
        return hash(frozenset(self.types))


class ProductType(Type):
    """Implements a product type, i.e. a record / tuple / struct"""

    def __init__(self, types):
        self.types = tuple(types)

    def __repr__(self):
        return "(%s)" % "*".join(map(repr, self.types))

    def __hash__(self):
        return hash(self.types)

    @classmethod
    def create(cls, types):
        return cls(types)


class ContainerType(DataType):
    """Base class for containers, such as generics."""

    @abstractmethod
    def __getitem__(self, other):
        ...


class Variance(Enum):
    Covariant = auto()
    Contravariant = auto()
    Invariant = auto()


class GenericType(ContainerType):
    """Implements a generic type. i.e. a container for items of a specific type.

    For any two generic types a[i] and b[j], it's true that a[i] <= b[j] iff a <= b and i <= j.
    """

    base: Type
    item: Union[type, Type]
    variance: Variance

    def __init__(self, base: Type, item: Union[type, Type], variance):
        assert isinstance(item, (Type, type)), item
        if isinstance(base, GenericType):
            if not item <= base.item:
                raise TypeError(
                    f"Expecting new generic to be a subtype of base, but {item} </= {base.item}"
                )
            base = base.base

        self.base = base
        self.item = item
        self.variance = variance

    def __repr__(self):
        if self.item is All:
            return str(self.base)
        return "%r[%r]" % (self.base, self.item)

    def __getitem__(self, item):
        return type(self)(self, item, self.variance)

    def __hash__(self):
        return hash((self.base, self.item))


class PhantomType(Type):
    """Implements a base for phantom types.

    A phantom type is a "meta" type that can wrap existing types,
    but it is transparent (subtype checks may skip over it), and has no effect otherwise.
    """

    def __getitem__(self, other):
        return PhantomGenericType(self, other)


class PhantomGenericType(Type):
    """Implements a generic phantom type, for carrying metadata within the type signature.

    For any phantom type p[i], it's true that p[i] <= p but also p[i] <= i and i <= p[i].
    """

    def __init__(self, base, item=All):
        self.base = base
        self.item = item


SamplerType = Callable[[Sequence], Sequence]


class Validator(ABC):
    """Defines the validator interface."""

    def validate_instance(self, obj, sampler: Optional[SamplerType] = None):
        """Validates obj, raising a TypeMismatchError if it does not conform.

        If sampler is provided, it will be applied to the instance in order to
        validate only a sample of the object. This approach may validate much faster,
        but might miss anomalies in the data.
        """
        if not self.test_instance(obj, sampler):
            raise TypeMismatchError(obj, self)

    @abstractmethod
    def test_instance(self, obj, sampler=None):
        """Tests obj, returning a True/False for whether it conforms or not.

        If sampler is provided, it will be applied to the instance in order to
        validate only a sample of the object.
        """
        # try:
        #     self.validate_instance(obj, sampler)
        #     return True
        # except TypeMismatchError:
        #     return False


class Constraint(Validator, Type):
    """Defines a constraint, which activates during validation."""

    def __init__(self, for_type, predicates):
        self.type = for_type
        self.predicates = predicates

    def validate_instance(self, inst, sampler=None):
        """Makes sure the instance conforms by applying it to all the predicates."""
        self.type.validate_instance(inst, sampler)

        for p in self.predicates:
            if not p(inst):
                raise TypeMismatchError(inst, self)

    def test_instance(self, inst, sampler=None):
        """Makes sure the instance conforms by applying it to all the predicates."""
        if not self.type.test_instance(inst, sampler):
            return False

        for p in self.predicates:
            if not p(inst):
                return False
        return True


# fmt: off
@dp
def le(self, other):
    return NotImplemented

@dp(priority=-1)
def le(self: Type, other: Type):
    return self == other

@dp
def ge(self, other):
    return le(other, self)

@dp
def eq(self, other):
    return NotImplemented

@dp
def eq(self: SumType, other: SumType):
    return self.types == other.types

@dp
def eq(self: ProductType, other: ProductType):
    return self.types == other.types

@dp
def eq(self: GenericType, other: GenericType):
    return self.base == other.base and self.item == other.item

@dp
def eq(self: GenericType, other: Type):
    return self.item is All and self.base == other

@dp
def eq(self: PhantomGenericType, other: PhantomGenericType):
    return self.base == other.base and self.item == other.base


# le() for AllType & AnyType


@dp(priority=100)
def le(self: Type, other: AllType):
    # All contains all types
    return True

@dp
def le(self: type, other: AllType):
    # All contains all types
    return True

@dp(priority=2)
def le(self: Type, other: AnyType):
    # Any may be a superset of any type
    return True

@dp
def le(self: type, other: AnyType):
    # Any may be a superset of any type
    return True

@dp(priority=1)
def le(self: AnyType, other: Type):
    # Any may be a subset of any type
    return True


# le() for SumType


@dp(priority=51)
def le(self: SumType, other: Type):
    return all(t <= other for t in self.types)

@dp(priority=50)
def le(self: Type, other: SumType):
    return any(self <= t for t in other.types)


# le() for ProductType


@dp
def le(self: ProductType, other: ProductType):
    if len(self.types) != len(other.types):
        return False

    return all(t1 <= t2 for t1, t2 in zip(self.types, other.types))


# le() for GenericType


@dp
def le(self: GenericType, other: GenericType):
    if self.variance == Variance.Covariant:
        return self.base <= other.base and self.item <= other.item
    elif self.variance == Variance.Contravariant:
        return self.base <= other.base and self.item >= other.item
    elif self.variance == Variance.Invariant:
        return self.base <= other.base and self.item == other.item
    raise RuntimeError()

@dp
def le(self: GenericType, other: Type):
    return self.base <= other

@dp
def le(self: Type, other: GenericType):
    return other.item is Any and self <= other.base


# le() for PhantomType and PhantomGenericType


@dp(priority=1)
def le(self: Type, other: PhantomGenericType):
    return self <= other.item

@dp
def le(self: PhantomGenericType, other: Type):
    return self.item <= other

@dp
def le(self: PhantomGenericType, other: PhantomType):
    # Only phantom types can match the base of a phantom-generic
    return self.base <= other or self.item <= other

# le() for Constraint

@dp
def le(self: Constraint, other: Constraint):
    # Arbitrary predicates prevent it from being a superclass
    return self == other

@dp(priority=1)
def le(self: Constraint, other: Type):
    return self.type <= other


Type.__eq__ = eq
Type.__le__ = le
Type.__ge__ = ge

# fmt: on
