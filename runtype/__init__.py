from .dataclass import dataclass
from .dispatch import DispatchError, MultiDispatch
from .validation import PythonTyping, TypeSystem, TypeMismatchError, assert_isa, isa, issubclass
from .pytypes import Constraint, String, Int

__version__ = "0.2.3"


def Dispatch(typesystem: TypeSystem = PythonTyping()):
    """Creates a decorator attached to a dispatch group,
    that when applied to a function, enables multiple-dispatch for it.

    Parameters:
        typesystem (Typesystem): Which type-system to use for dispatch. Default is Python's.

    Example:
        ::

            >>> from runtype import Dispatch
            >>> dp = Dispatch()

            >>> @dp
            ... def add1(i: Optional[int]):
            ...     return i + 1

            >>> @dp
            ... def add1(s: Optional[str]):
            ...     return s + "1"

            >>> @dp
            ... def add1(a):  # Any, which is the least-specific
            ...     return (a, 1)

            >>> add1(1)
            2

            >>> add1("1")
            11

            >>> add1(1.0)
            (1.0, 1)


    """

    return MultiDispatch(typesystem)


