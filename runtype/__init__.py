from typing import Callable, TYPE_CHECKING

from .dataclass import dataclass
from .dispatch import DispatchError, MultiDispatch
from .validation import (PythonTyping, TypeSystem, TypeMismatchError,
                         assert_isa, isa, issubclass, validate_func, is_subtype)
from .pytypes import Constraint, String, Int, cv_type_checking

__version__ = "0.4.0"
__all__ = (
    'dataclass',
    'DispatchError', 'MultiDispatch',
    'PythonTyping', 'TypeSystem', 'TypeMismatchError',
    'assert_isa', 'isa', 'issubclass', 'validate_func', 'is_subtype', 'cv_type_checking',
    'Constraint', 'String', 'Int',
    'Dispatch',
)

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



typesystem: TypeSystem = PythonTyping()

class PythonDispatch:
    def __init__(self):
        self.by_module = {}

    def decorate(self, f: Callable) -> Callable:
        """A decorator that enables multiple-dispatch for the given function.

        The dispatch namespace is unique for each module, so there can be no name
        collisions for functions defined across different modules.
        Users that wish to share a dispatch across modules, should use the
        `Dispatch` class.

        Parameters:
            f (Callable): Function to enable multiple-dispatch for

        Returns:
            the decorated function

        Example:
            ::

                >>> from runtype import multidispatch as md

                >>> @md
                ... def add1(i: Optional[int]):
                ...     return i + 1

                >>> @md
                ... def add1(s: Optional[str]):
                ...     return s + "1"

                >>> @md
                ... def add1(a):  # accepts any type (least-specific)
                ...     return (a, 1)

                >>> add1(1)
                2

                >>> add1("1")
                11

                >>> add1(1.0)
                (1.0, 1)


        """
        module = f.__module__
        if module not in self.by_module:
            self.by_module[module] = MultiDispatch(typesystem)
        return self.by_module[module](f)

python_dispatch = PythonDispatch()

multidispatch_final = python_dispatch.decorate
if TYPE_CHECKING:
    from typing import overload as multidispatch
else:
    multidispatch = python_dispatch.decorate
