from typing import Any, Generic, TypeVar

T = TypeVar("T")

class TypeSystem(Generic[T]):
    def isinstance(self, obj: object, t: T) -> bool:
        return self.issubclass(self.get_type(obj), t)

    def issubclass(self, t1: T, t2: T) -> bool:
        raise NotImplementedError()

    def to_canonical_type(self, t: T) -> T:
        return t

    def get_type(self, obj: object) -> T:
        raise NotImplementedError()

    default_type: T
    any_type: T



class PythonBasic(TypeSystem[type]):
    isinstance = isinstance   # type: ignore[assignment]
    issubclass = issubclass   # type: ignore[assignment]
    get_type = type           # type: ignore[assignment]
    default_type = object
    any_type = Any
