

class TypeSystem:
    def isinstance(self, obj, t):
        return self.issubclass(self.get_type(obj), t)

    def issubclass(self, t1, t2):
        raise NotImplementedError()

    def canonize_type(self, t):
        raise NotImplementedError()

    def get_type(self, obj):
        raise NotImplementedError()



class PythonBasic(TypeSystem):
    isinstance = isinstance
    issubclass = issubclass
    canonize_type = lambda x:x
    get_type = type
