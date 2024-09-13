from typing import Any

class TypeSystem:
    def isinstance(self, obj, t: type) -> bool:
        return self.issubclass(self.get_type(obj), t)

    def issubclass(self, t1: type, t2: type) -> bool:
        raise NotImplementedError()

    def to_canonical_type(self, t: type) -> type:
        return t

    def get_type(self, obj) -> type:
        raise NotImplementedError()

    default_type: type = NotImplemented
    any_type: type = NotImplemented



class PythonBasic(TypeSystem):
    isinstance = isinstance
    issubclass = issubclass
    get_type = type
    default_type = object
    any_type = Any
