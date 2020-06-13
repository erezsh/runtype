

class TypeSystem:
    def isinstance(self, obj, t):
        return self.issubclass(self.get_type(obj), t)

    def issubclass(self, t1, t2):
        raise NotImplementedError()

    def canonize_type(self, t):
        return t

    def get_type(self, obj):
        raise NotImplementedError()

    default_type = NotImplemented



class PythonBasic(TypeSystem):
    isinstance = isinstance
    issubclass = issubclass
    get_type = type
    default_type = object
