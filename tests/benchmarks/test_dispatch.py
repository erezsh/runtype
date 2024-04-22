import textwrap

import pytest

from runtype import Dispatch
try:
    import plum
except ImportError:
    class plum:
        dispatch = None

dispatch = Dispatch()

each_dispatcher = pytest.mark.parametrize("libname,dispatcher", [("stdlib (if-else + isinstance)", None), ('plum', plum.dispatch), ('runtype', dispatch)])


@each_dispatcher
@pytest.mark.benchmark(group="dispatch 1 argument, 2 branches $$ div:2 group:A")
def test_dispatch_minimal(benchmark, libname, dispatcher):
    def _test_dispatch_minimal(f):
        return f(1), f("1")

    if libname.startswith("stdlib"):
        def f_minimal(x):
            if isinstance(x, int):
                return "int"
            elif isinstance(x, str):
                return "str"
            raise RuntimeError()
    else:
        assert dispatcher
        @dispatcher
        def f_minimal(x: int):
            return "int"

        @dispatcher
        def f_minimal(x: str):
            return "str"
    
    res = benchmark(_test_dispatch_minimal, f_minimal)
    assert res == ("int", "str",)


class _Str(str):
    pass

@each_dispatcher
@pytest.mark.benchmark(group="dispatch 1 argument, 8 branches $$ div:8 group:A")
def test_dispatch_8_branches(benchmark, libname, dispatcher):
    def _test_dispatch_many_funcs(f):
        return f(1), f(1.0), f(b""), f("1"), f(_Str("1")), f(()), f([]), f(None)

    if libname.startswith("stdlib"):
        def f_manyf(x):
            if x is None:
                return "none"
            elif isinstance(x, int):
                return "int"
            elif isinstance(x, float):
                return "float"
            elif isinstance(x, bytes):
                return "bytes"
            elif isinstance(x, _Str):
                return "_Str"
            elif isinstance(x, str):
                return "str"
            elif isinstance(x, tuple):
                return "tuple"
            return "any"
    else:
        @dispatcher
        def f_manyf(x: None):
            return "none"

        @dispatcher
        def f_manyf(x: int):
            return "int"

        @dispatcher
        def f_manyf(x: float):
            return "float"

        @dispatcher
        def f_manyf(x: bytes):
            return "bytes"

        @dispatcher
        def f_manyf(x: str):
            return "str"

        @dispatcher
        def f_manyf(x: _Str):
            return "_Str"

        @dispatcher
        def f_manyf(x: tuple):
            return "tuple"

        @dispatcher
        def f_manyf(x):
            return "any"
    
    res = benchmark(_test_dispatch_many_funcs, f_manyf)
    assert res == ("int", "float", "bytes", "str", "_Str", "tuple", "any", "none")


@each_dispatcher
@pytest.mark.benchmark(group="dispatch 1 argument, with 32 branches $$ div:32 group:A")
def test_dispatch_32_branches(benchmark, libname, dispatcher):
    num_classes = 32

    class_names = [f"C{i}" for i in range(num_classes)]

    # Definition of classes C0 to C31
    context = {'dispatcher': dispatcher}
    for name in class_names:
        context[name] = type(name, (), {})

    if libname.startswith("stdlib"):
        branches = ''.join(textwrap.dedent(f"""
        elif isinstance(x, {name}):
            return "{name}"
        """) for name in class_names).strip()[2:]
        func = textwrap.dedent("""
        def f(x):
            %s
            raise RuntimeError("Unhandled class")
        """) % (textwrap.indent('\n'+branches, '    '),)
        exec(func, context)
    else:
        branches = textwrap.dedent(''.join(f"""
        @dispatcher
        def f(x: {name}):
            return "{name}"
        """ for name in class_names
        ))
        exec(branches, context)

    all_classes = [context[name] for name in class_names]

    def _test_dispatch_32_branches(f):
        return [f(cls()) for cls in all_classes]

    res = benchmark(_test_dispatch_32_branches, context['f'])
    assert res == [c.__name__ for c in all_classes]


@each_dispatcher
@pytest.mark.benchmark(group="dispatch 2 branches, union of 8 types $$ div:16 group:B")
def test_dispatch_union(benchmark, libname, dispatcher):
    num_classes = 16
    union_size = 8

    class_names = [f"C{i}" for i in range(num_classes)]
    class_names_by_4 = [tuple(class_names[i:i + union_size]) for i in range(0, len(class_names), union_size)]
    assert len(class_names_by_4) == num_classes / union_size

    # Definition of classes C0 to C31
    context = {'dispatcher': dispatcher}
    for name in class_names:
        context[name] = type(name, (), {})

    if libname.startswith("stdlib"):
        branches = ''.join(textwrap.dedent(f"""
        elif isinstance(x, {'|'.join(classes)}):
            return "{classes[0]}"
        """) for classes in class_names_by_4).strip()[2:]
        func = textwrap.dedent("""
        def f(x):
            %s
            raise RuntimeError("Unhandled class")
        """) % (textwrap.indent('\n'+branches, '    '),)
        exec(func, context)
    else:
        branches = textwrap.dedent(''.join(f"""
        @dispatcher
        def f(x: {'|'.join(classes)}):
            return "{classes[0]}"
        """ for classes in class_names_by_4
        ))
        exec(branches, context)

    all_classes = [context[name] for name in class_names]

    def _test_dispatch_32_branches(f):
        return [f(cls()) for cls in all_classes]

    res = benchmark(_test_dispatch_32_branches, context['f'])
    assert res == [x for classes in class_names_by_4 for x in [classes[0]]*union_size]

def _test_dispatch_many_args(f):
    return (
        f(1, 1, 1, '1', '1'),
        f(1.0, 1.0, 1.0, '1', '1'),
    )

@each_dispatcher
@pytest.mark.benchmark(group="dispatch 5 arguments, 2 branches $$ div:2 group:A")
def test_dispatch_many_args(benchmark, libname, dispatcher):
    if libname.startswith("stdlib"):
        def f_many_args(x, y, z, name, extra):
            if isinstance(x, int) and isinstance( y, int) and isinstance( z, int) and isinstance( name, str) and isinstance( extra, str):
                return "int"
            elif isinstance(x, float) and isinstance( y, float) and isinstance( z, float) and isinstance( name, str) and isinstance(extra, str):
                return "float"
            raise RuntimeError()

    else:
        @dispatcher
        def f_many_args(x: int, y: int, z: int, name: str, extra: str):
            return "int"

        @dispatcher
        def f_many_args(x: float, y: float, z: float, name: str, extra: str):
            return "float"
    
    res = benchmark(_test_dispatch_many_args, f_many_args)
    assert res == ("int", "float",)



def _test_dispatch_specificity(f):
    return (
        f('1', '1'),
        f('1', 1),
        f('1', _Str('1')),
        f(_Str('1'), _Str('1')),
        f(1, _Str('1')),
        f(_Str('1'), 1),
        f(1, '1'),
        f(1, 1),
    )

@each_dispatcher
@pytest.mark.benchmark(group="dispatch with mixed specificity (8 branches) $$ div:8 group:A")
def test_dispatch_specificity(benchmark, libname, dispatcher):
    if libname.startswith("stdlib"):
        return NotImplemented

    @dispatcher
    def f_specificity(x: str, y: str):
        return "str-str"

    @dispatcher
    def f_specificity(x: str, y):
        return "str-any"

    @dispatcher
    def f_specificity(x: str, y: _Str):
        return "str-Str"

    @dispatcher
    def f_specificity(x: _Str, y: _Str):
        return "str-Str"

    @dispatcher
    def f_specificity(x, y: _Str):
        return "any-Str"

    @dispatcher
    def f_specificity(x: _Str, y):
        return "Str-any"

    @dispatcher
    def f_specificity(x, y: str):
        return "any-str"

    @dispatcher
    def f_specificity(x, y):
        return "any-any"
    
    res = benchmark(_test_dispatch_specificity, f_specificity)