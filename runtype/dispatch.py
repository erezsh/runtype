from collections import defaultdict
import inspect
from functools import wraps

from .isa import isa, issubclass, canonize_type

class DispatchError(Exception):
    pass

class Dispatch:
    """Create a decorator attached to a dispatch group,
    that when applied to a function, enables multiple-dispatch for it.

    Example:
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
    def __init__(self):
        self.roots = defaultdict(TypeTree)

    def __call__(self, f):
        root = self.roots[f.__name__]
        root.name = f.__name__

        root.define_function(f)

        @wraps(f)
        def dispatched_f(*args, **kw):
            f = root.find_function_cached(args)
            return f(*args, **kw)

        return dispatched_f


class TypeTree:
    def __init__(self):
        self.root = TypeNode()
        self._cache = {}

    def find_function(self, args):
        nodes = [self.root]
        for a in args:
            nodes = [n for node in nodes for n in node.follow_arg(a)]

        funcs = [node.func for node in nodes if node.func]

        if len(funcs) == 0:
            raise DispatchError(f"Function '{self.name}' not found for signature {get_args_simple_signature(args)}")
        elif len(funcs) > 1:
            f, _sig = max_cmp(funcs, choose_most_specific_function)
        else:
            (f, _sig) ,= funcs
        return f

    def find_function_cached(self, args):
        "Memoized version of find_function"
        sig = get_args_simple_signature(args)
        try:
            return self._cache[sig]
        except KeyError:
            f = self.find_function(args)
            self._cache[sig] = f
            return f


    def define_function(self, f):
        for signature in get_func_signatures(f):
            node = self.root
            for t in signature:
                node = node.follow_type[t]

            if node.func is not None:
                raise ValueError(f"Function {f.__name__} matches existing signature: {signature}!")
            node.func = f, signature


class TypeNode:
    def __init__(self):
        self.follow_type = defaultdict(TypeNode)
        self.func = None

    def follow_arg(self, arg):
        for type_, tree in self.follow_type.items():
            if isa(arg, type_):
                yield tree


def max_cmp(lst, f):
    best = lst[0]
    for i in lst[1:]:
        best = f(i, best)
    return best

def choose_most_specific_function(func1, func2):
    f1, sig1 = func1
    f2, sig2 = func2

    most_specific = set()
    for i, pair in enumerate(zip(sig1, sig2)):
        a, b = pair
        if a == b:
            continue

        if issubclass(a, b):
            x = -1  # left
        elif issubclass(b, a):
            x = 1   # right
        else:
            n = f1.__name__
            raise DispatchError(f"Ambiguous dispatch in '{n}', argument #{i+1}: Unable to resolve the specificity of the types:\n\t- {a}\n\t- {b}")

        most_specific.add(x)

    if most_specific == {-1, 1}:    # Both left & right were chosen?
        n = f1.__name__
        raise DispatchError(f"Ambiguous dispatch in '{n}': Unable to resolve the specificity of the functions:\n\t- {n}{tuple(sig1)}\n\t- {n}{tuple(sig2)}")

    elif most_specific == {-1}:
        return f1, sig1

    assert most_specific == {1}, (most_specific, sig1, sig2)
    return f2, sig2


def get_func_signatures(f):
    sig = inspect.signature(f)
    typesigs = []
    typesig = []
    for p in sig.parameters.values():
        # if p.kind is p.VAR_KEYWORD or p.kind is p.VAR_POSITIONAL:
        #     raise TypeError("Dispatch doesn't support *args or **kwargs yet")

        t = p.annotation
        if t is sig.empty:
            t = object
        else:
            t = canonize_type(t)
        # elif not isinstance(t, type):
        #     raise TypeError("Annotation isn't a type")

        if p.default is not p.empty:
            # From now on, everything is optional
            typesigs.append(list(typesig))

        typesig.append(t)

    typesigs.append(typesig)
    return typesigs


def get_args_simple_signature(args):
    return tuple(type(a) for a in args)
