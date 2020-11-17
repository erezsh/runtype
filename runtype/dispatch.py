from collections import defaultdict
import inspect
from functools import wraps

class DispatchError(Exception):
    pass

class MultiDispatch:
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
    def __init__(self, typesystem):
        self.roots = defaultdict(TypeTree)
        self.typesystem = typesystem

    def __call__(self, f):
        root = self.roots[f.__name__]
        root.name = f.__name__
        root.typesystem = self.typesystem

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
        self.name = None
        self.typesystem = None

    def get_args_simple_signature(self, args):
        get_type = self.typesystem.get_type
        return tuple(get_type(a) for a in args)

    def find_function(self, args):
        nodes = [self.root]
        for a in args:
            nodes = [n for node in nodes for n in node.follow_arg(a, self.typesystem)]

        funcs = [node.func for node in nodes if node.func]

        if len(funcs) == 0:
            raise DispatchError(f"Function '{self.name}' not found for signature {self.get_args_simple_signature(args)}")
        elif len(funcs) > 1:
            f, _sig = self.choose_most_specific_function(*funcs)
        else:
            (f, _sig) ,= funcs
        return f


    def find_function_cached(self, args):
        "Memoized version of find_function"
        sig = self.get_args_simple_signature(args)
        try:
            return self._cache[sig]
        except KeyError:
            f = self.find_function(args)
            self._cache[sig] = f
            return f


    def define_function(self, f):
        for signature in self.get_func_signatures(f):
            node = self.root
            for t in signature:
                node = node.follow_type[t]

            if node.func is not None:
                code_obj = node.func[0].__code__
                raise ValueError(f"Function {f.__name__} at {code_obj.co_filename}:{code_obj.co_firstlineno} matches existing signature: {signature}!")
            node.func = f, signature


    def get_func_signatures(self, f):
        sig = inspect.signature(f)
        typesigs = []
        typesig = []
        for p in sig.parameters.values():
            # if p.kind is p.VAR_KEYWORD or p.kind is p.VAR_POSITIONAL:
            #     raise TypeError("Dispatch doesn't support *args or **kwargs yet")

            t = p.annotation
            if t is sig.empty:
                t = self.typesystem.default_type
            else:
                # Canonize to detect more collisions on construction, instead of during dispatch
                t = self.typesystem.canonize_type(t)
            # elif not isinstance(t, type):
            #     raise TypeError("Annotation isn't a type")

            if p.default is not p.empty:
                # From now on, everything is optional
                typesigs.append(list(typesig))

            typesig.append(t)

        typesigs.append(typesig)
        return typesigs

    def choose_most_specific_function(self, *funcs):
        issubclass = self.typesystem.issubclass

        class IsSubclass:
            def __init__(self, k):
                self.i, self.t = k

            def __lt__(self, other):
                return issubclass(self.t, other.t)

        most_specific_per_param = []
        sigs = [f[1] for f in funcs]
        for arg_idx, zipped_params in enumerate(zip(*sigs)):
            if all_eq(zipped_params):
                continue
            x = sorted(enumerate(zipped_params), key=IsSubclass)
            ms_i, ms_t = x[0]   # Most significant index and type
            ms_set = {ms_i}     # Init set of indexes of most significant params
            for i, t in x[1:]:
                if ms_t == t:
                    ms_set.add(i)   # Add more indexes with the same type
                elif issubclass(t, ms_t) or not issubclass(ms_t, t):
                    # Cannot resolve ordering of these two types
                    n = funcs[0][0].__name__
                    msg = f"Ambiguous dispatch in '{n}', argument #{arg_idx+1}: Unable to resolve the specificity of the types: \n\t- {t}\n\t- {ms_t}"
                    raise DispatchError(msg)

            most_specific_per_param.append(ms_set)

        # Is there only one function that matches each and every parameter?
        most_specific = set.intersection(*most_specific_per_param)
        if len(most_specific) != 1:
            n = funcs[0][0].__name__
            msg = f"Ambiguous dispatch in '{n}': Unable to resolve the specificity of the functions"
            msg += ''.join(f'\n\t- {n}{tuple(f[1])}' for f in funcs)
            raise DispatchError(msg)

        ms ,= most_specific
        return funcs[ms]

def all_eq(xs):
    a = xs[0]
    for b in xs[1:]:
        if a != b:
            return False
    return True

class TypeNode:
    def __init__(self):
        self.follow_type = defaultdict(TypeNode)
        self.func = None

    def follow_arg(self, arg, ts):
        for type_, tree in self.follow_type.items():
            if ts.isinstance(arg, type_):
                yield tree

