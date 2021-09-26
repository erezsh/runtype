from .dataclass import dataclass
from .dispatch import DispatchError, MultiDispatch
from .isa import PythonTyping, TypeMismatchError, assert_isa, isa, issubclass
from .pytypes import Constraint, String, Int


def Dispatch(typesystem=PythonTyping()):
    return MultiDispatch(typesystem)


__version__ = "0.2.1"
