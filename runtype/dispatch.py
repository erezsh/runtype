from collections import defaultdict
from functools import wraps
from typing import Any, Dict, Callable, Sequence
from operator import itemgetter
import warnings

from dataclasses import dataclass

from .utils import get_func_signatures
from .typesystem import TypeSystem


class DispatchError(Exception):
    "Thrown whenever a dispatch fails. Contains text describing the conflict."


# TODO: Remove test_subtypes, replace with support for Type[], like isa(t, Type[t])
class MultiDispatch:
    """Creates a dispatch group for multiple dispatch

    Parameters:
        typesystem (Typesystem): Which type-system to use for dispatch.
        test_subtypes: indices of params that should be matched by subclass instead of isinstance.
                        (will be soon deprecated and replaced by using Type[..] annotations)
    """

    def __init__(self, typesystem: TypeSystem, test_subtypes: Sequence[int] = ()):
        self.fname_to_tree: Dict[str, TypeTree] = {}
        self.typesystem: TypeSystem = typesystem
        if test_subtypes:
            warnings.warn("The test_subtypes option is deprecated and will be removed in the future."
                          "Use typing.Type[t] instead.", DeprecationWarning)

        self.test_subtypes = test_subtypes

    def __call__(self, func=None, *, priority=None):
        """Decorate the function

        Warning: Priority is still an experimental feature
        """
        if func is None:
            if priority is None:
                raise ValueError(
                    "Must either provide a function to decorate, or set a priority"
                )
            return MultiDispatchWithOptions(self, priority=priority)

        if priority is not None:
            raise ValueError(
                "Must either provide a function to decorate, or set a priority"
            )

        fname = func.__qualname__
        try:
            tree = self.fname_to_tree[fname]
        except KeyError:
            tree = self.fname_to_tree[fname] = TypeTree(
                fname, self.typesystem, self.test_subtypes
            )

        tree.define_function(func)
        find_function_cached = tree.find_function_cached

        @wraps(func)
        def dispatched_f(*args, **kw):
            # Done in two steps to help debugging
            f = find_function_cached(args)
            return f(*args, **kw)

        dispatched_f.__dispatcher__ = self
        return dispatched_f

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass


@dataclass
class MultiDispatchWithOptions:
    dispatch: MultiDispatch
    priority: int

    def __call__(self, f):
        f.__dispatch_priority__ = self.priority
        return self.dispatch(f)


class TypeNode:
    def __init__(self):
        self.follow_type = defaultdict(TypeNode)
        self.func = None

    def follow_arg(self, arg, ts, test_subtype=False):
        for type_, tree in self.follow_type.items():
            if test_subtype:
                if ts.issubclass(arg, type_):
                    yield tree
            elif ts.isinstance(arg, type_):
                yield tree


class TypeTree:
    root: TypeNode
    name: str
    _cache: Dict[tuple, Callable]
    typesystem: TypeSystem
    test_subtypes: Sequence[int]

    def __init__(self, name: str, typesystem: TypeSystem, test_subtypes: Sequence[int]):
        self.root = TypeNode()
        self._cache = {}
        self.name = name
        self.typesystem = typesystem
        self.test_subtypes = test_subtypes
        self._get_type = self.typesystem.get_type

        if self.test_subtypes:
            # Deprecated!!
            self.find_function_cached = self._old_find_function_cached

    def get_arg_types(self, args):
        if self.test_subtypes:
            # TODO can be made more efficient
            return tuple(
                (a if i in self.test_subtypes else self._get_type(a))
                for i, a in enumerate(args)
            )

        return tuple(map(self._get_type, args))

    def find_function(self, args):
        nodes = [self.root]
        for i, a in enumerate(args):
            nodes = [
                n
                for node in nodes
                for n in node.follow_arg(
                    a, self.typesystem, test_subtype=i in self.test_subtypes
                )
            ]

        funcs = [node.func for node in nodes if node.func]

        if len(funcs) == 0:
            raise DispatchError(
                f"Function '{self.name}' not found for signature {self.get_arg_types(args)}"
            )
        elif len(funcs) > 1:
            f, _sig = self.choose_most_specific_function(args, *funcs)
        else:
            ((f, _sig),) = funcs
        return f

    def _old_find_function_cached(self, args):
        "Memoized version of find_function"
        sig = self.get_arg_types(args)
        try:
            return self._cache[sig]
        except KeyError:
            f = self.find_function(args)
            self._cache[sig] = f
            return f

    def find_function_cached(self, args):
        "Memoized version of find_function"
        try:
            return self._cache[tuple(map(self._get_type, args))]
        except KeyError:
            sig = tuple(map(self._get_type, args))
            f = self.find_function(args)
            self._cache[sig] = f
            return f

    def define_function(self, f):
        for signature in get_func_signatures(self.typesystem, f):
            node = self.root
            for t in signature:
                if not isinstance(t, type):
                    # XXX this is a temporary fix for preventing certain types from being used for dispatch
                    if not getattr(t, 'ALLOW_DISPATCH', True):
                        raise ValueError(f"Type {t} cannot be used for dispatch")
                node = node.follow_type[t]

            if node.func is not None:
                code_obj = node.func[0].__code__
                raise ValueError(
                    f"Function {f.__name__} at {code_obj.co_filename}:{code_obj.co_firstlineno} matches existing signature: {signature}!"
                )
            node.func = f, signature

    def choose_most_specific_function(self, args, *funcs):
        issubclass = self.typesystem.issubclass
        any_type = self.typesystem.any_type

        class IsSubclass:
            def __init__(self, k):
                self.i, self.t = k

            def __lt__(self, other):
                if self.t is any_type:
                    return False
                return issubclass(self.t, other.t)

        most_specific_per_param = []
        sigs = [f[1] for f in funcs]
        for arg_idx, zipped_params in enumerate(zip(*sigs)):
            if all_eq(zipped_params):
                continue
            x = sorted(enumerate(zipped_params), key=IsSubclass)
            ms_i, ms_t = x[0]  # Most significant index and type
            ms_set = {ms_i}  # Init set of indexes of most significant params
            for i, t in x[1:]:
                if ms_t == t:
                    # Add more indexes with the same type
                    ms_set.add(i)
                elif (issubclass(t, ms_t) and t is not any_type) or not issubclass(ms_t, t):
                    # Possibly ambiguous. We might throw an error below
                    # TODO secondary candidates should still obscure less specific candidates
                    #      by only considering the top match, we are ignoring them
                    ms_set.add(i)

            most_specific_per_param.append(ms_set)

        # Is there only one function that matches each and every parameter?
        most_specific = set.intersection(*most_specific_per_param)
        if len(most_specific) == 1:
            (ms,) = most_specific
            return funcs[ms]

        ambig_funcs = [funcs[i] for i in set.union(*most_specific_per_param)]
        assert len(ambig_funcs) > 1
        p_ambig_funcs = [
            (getattr(f, "__dispatch_priority__", 0), f, params)
            for f, params in ambig_funcs
        ]
        p_ambig_funcs.sort(key=itemgetter(0), reverse=True)
        if p_ambig_funcs[0][0] > p_ambig_funcs[1][0]:
            # If one item has a higher priority than all others, choose it
            p, f, params = p_ambig_funcs[0]
            return f, params

        # Could not resolve ambiguity. Throw error
        n = funcs[0][0].__name__
        msg = f"Ambiguous dispatch in '{n}': Unable to resolve the specificity of the functions"
        msg += "".join(
            f"\n\t- {n}{tuple(params)} [priority={p}]" for p, f, params in p_ambig_funcs
        )
        msg += f"\nFor arguments: {args}"
        raise DispatchError(msg)


def all_eq(xs):
    a = xs[0]
    for b in xs[1:]:
        if a != b:
            return False
    return True
