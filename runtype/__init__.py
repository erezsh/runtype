from .isa import isa, issubclass, PythonTyping
from .dispatch import MultiDispatch, DispatchError
from .dataclass import dataclass


def Dispatch(typesystem=PythonTyping()):
    return MultiDispatch(typesystem)



__version__ = "0.1.1"
