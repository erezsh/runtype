from .isa import isa, issubclass, assert_isa, PythonTyping, TypeMismatchError
from .dispatch import MultiDispatch, DispatchError
from .dataclass import dataclass


def Dispatch(typesystem=PythonTyping()):
    return MultiDispatch(typesystem)



__version__ = "0.1.12"
