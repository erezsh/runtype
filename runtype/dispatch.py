from collections import defaultdict
import inspect
from functools import wraps

from .isa import isa, issubclass, canonize_type

class DispatchError(Exception):
    pass

class Dispatch:
    def __init__(self):
        self.roots = defaultdict(TypeTree)

    def __call__(self, f):
        root = self.roots[f.__name__]

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

        funcs = [node.func for node in nodes]

        if len(funcs) == 0:
            raise DispatchError("Function not found")
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
        signature = list(get_func_simple_signature(f))
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
    for pair in zip(sig1, sig2):
        a, b = pair
        if a == b:
            continue

        if issubclass(a, b):
            x = -1
        elif issubclass(b, a):
            x = 1
        else:
            raise DispatchError(f"Ambiguous dispatch: Unable to resolve specificity of types: {a}, {b}")

        most_specific.add(x)

    if most_specific == {-1, 1}:
        raise DispatchError("Ambiguous dispatch")

    elif most_specific == {-1}:
        return f1, sig1

    assert most_specific == {1}, (most_specific, sig1, sig2)
    return f2, sig2


def get_func_simple_signature(f):
    sig = inspect.signature(f)
    for p in sig.parameters.values():
        t = p.annotation
        if t is inspect._empty:
            t = object
        else:
            t = canonize_type(t)
        # elif not isinstance(t, type):
        #     raise TypeError("Annotation isn't a type")
        yield t

def get_args_simple_signature(args):
    return tuple(type(a) for a in args)
