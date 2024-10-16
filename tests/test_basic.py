import unittest
from unittest import TestCase
from collections import abc
import sys

import typing
from typing import Any, List, Dict, Tuple, Union, Optional, Callable, Set, FrozenSet, Sequence, Type, TypeVar, Generic
from collections.abc import Iterable
from dataclasses import FrozenInstanceError, field

import logging
logging.basicConfig(level=logging.INFO)

from runtype import Dispatch, DispatchError, dataclass, isa, is_subtype, issubclass, assert_isa, String, Int, validate_func, cv_type_checking, multidispatch
from runtype.dispatch import MultiDispatch
from runtype.dataclass import Configuration

try:
    import typing_extensions
except ImportError:
    typing_extensions = None


class TestIsa(TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        assert isa(1, int)
        assert issubclass(int, object)
        assert isa([1,2], List[int])
        assert isa([1,2], Sequence[int])
        assert not isa([1,"a"], List[int])
        assert not isa([1,2], List[str])
        assert isa(1, (int, str))
        assert not isa(1, (float, str))
        assert isa(int, Type[int])
        assert not isa(str, Sequence[int])

        self.assertRaises(TypeError, isa, 1, 1)
        self.assertRaises(TypeError, issubclass, 1, 1)

        assert isa(object, Any)
        assert isa(Any, object)

        assert issubclass(object, Any)
        assert issubclass(Any, object)
        assert issubclass(Callable, Callable)

        assert isa({'a': 1}, Dict[str, int])
        assert not isa({'a': 1}, Dict[str, str])
        assert not isa({'a': 'a'}, Dict[str, int])
        assert isa(lambda:0, Callable)
        assert not isa(1, Callable)

        assert not issubclass(List[int], list)  # invariant
        assert issubclass(Tuple[int], tuple)
        assert issubclass(Tuple[int, int], tuple)
        assert not issubclass(tuple, Tuple[int])

        assert issubclass(Any, Any)
        assert issubclass(Any, int)
        assert issubclass(List[int], Any)

        assert issubclass(object, object)
        assert not issubclass(object, int)
        assert issubclass(List[int], object)


        # Tuples
        assert isa((3,), Tuple[int])
        assert isa((3, 5), Tuple[int, int])
        assert not isa((3, 5), Tuple[int, float])
        assert not isa((3, 5), Tuple[int])

        assert isa((3,), (Tuple[int], list))
        assert not isa([40, 2], Tuple[int, int])
        assert not issubclass(float, typing.Tuple[float, float])

        # Mappings
        assert issubclass(dict, abc.Mapping)
        assert issubclass(dict, typing.Mapping)
        assert isa({'a': 'b'}, typing.Mapping)
        assert isa({'a': 'b'}, typing.Mapping)
        assert isa({'a': 'b'}, typing.Mapping[str, str])
        assert not isa({'a': 'b'}, typing.Mapping[str, int])

        assert isa({'a': 'b'}, Dict[str, str])
        assert not isa({'a': 1}, Dict[str, str])
        assert not isa({2: 'a'}, Dict[str, str])
        assert isa({2: 'a'}, Dict[int, str])

        # Sets
        assert isa({'a'}, Set[str])
        assert not isa({'a'}, Set[int])
        assert not isa({'a'}, FrozenSet[str])

        assert isa(frozenset({'a'}), FrozenSet[str])
        assert not isa(frozenset({'a'}), FrozenSet[int])
        assert not isa(frozenset({'a'}), Set[int])


    def test_issubclass(self):
        assert not issubclass(List[Tuple], list)    # invariant
        assert issubclass(Sequence[Tuple], Sequence)

        if hasattr(typing, 'Annotated'):
            a = typing.Annotated[int, range(1, 10)]
            assert issubclass(a, int)
            assert issubclass(int, a)
            assert isa(1, a)

        assert issubclass(typing.Tuple, tuple)
        assert issubclass(typing.Tuple[int], tuple)
        assert issubclass(typing.Tuple[int, ...], tuple)
        assert issubclass(typing.Tuple[int], typing.Tuple[typing.Union[int, str]])
        assert issubclass(typing.Tuple[int, ...], typing.Tuple[typing.Union[int, str], ...])

    def test_issubclass_mutable(self):
        assert issubclass(typing.Dict[int, str], typing.MutableMapping[int, str])
        assert issubclass(typing.MutableMapping[int, str], typing.Mapping[int, str])

        assert issubclass(typing.List[int], typing.MutableSequence[int])
        assert issubclass(typing.MutableSequence[int], typing.Sequence[int])

        assert issubclass(typing.Set[int], typing.MutableSet[int])
        assert issubclass(typing.MutableSet[int], typing.AbstractSet[int])
 
    def test_issubclass_str_sequence(self):
        assert not issubclass(str, typing.MutableSequence[int])
        assert not issubclass(str, typing.Sequence[int])
        assert issubclass(str, typing.Sequence[str])

    def test_issubclass_tuple(self):
        # test class tuple
        t = int, float
        assert issubclass(int, t)
        assert issubclass(float, t)
        assert not issubclass(str, t)


    def test_assert(self):
        assert_isa(1, int)
        assert_isa("a", str)
        self.assertRaises(TypeError, assert_isa, 1, str)
        assert_isa([1,2], List[int])
        self.assertRaises(TypeError, assert_isa, [1,"2"], List[int])

    def test_tuple_ellipsis(self):
        assert_isa((1,2,3), Tuple[int, ...])
        self.assertRaises(TypeError, assert_isa, (1, "2"), Tuple[int, ...])

        assert issubclass(Tuple[str, ...], typing.Sequence[str])
        assert not issubclass(Tuple[str, ...], typing.Sequence[int])

        assert is_subtype(Tuple[str, str], Tuple[str, ...])
        assert not is_subtype(Tuple[str, int], Tuple[str, ...])

    @unittest.skipIf(sys.version_info < (3, 8), "Not supported before Python 3.8")
    def test_py38(self):
        assert isa('a', typing.Literal['a', 'b'])
        assert not isa('c', typing.Literal['a', 'b'])

        assert is_subtype(typing.Literal[1], typing.Literal[1,2])

    def test_validate_func(self):
        @validate_func
        def f(a: int, b: str, c: List[int] = []):
            return a,b,c

        f(1, "1", [1])
        self.assertRaises(TypeError, f, "1", 1, [1])
        self.assertRaises(TypeError, f, 1, "1", ["1"])

        @validate_func
        def f(a: List[int] = None):
            return a

        f([1, 2])
        f()
        self.assertRaises(TypeError, f, [1, None])

    def test_typing_extensions(self):
        if typing_extensions is None:
            logging.info("Skipping tests for typing extensions")
            return

        a = typing_extensions.Annotated[int, range(1, 10)]
        assert is_subtype(a, int)
        assert is_subtype(int, a)
        assert isa(1, a)

    @unittest.skipIf(not hasattr(typing, 'Literal'), "Literals not supported in this Python version")
    def test_literal_comparison(self):
        t1 = typing.Literal[1,2]
        t2 = Union[typing.Literal[1], typing.Literal[2]]

        assert is_subtype(t1, t2) 
        assert is_subtype(t2, t1) 

        assert is_subtype(Optional[typing.Literal[1]], typing.Literal[None, 1])
        assert is_subtype(typing.Literal[None, 1], Optional[typing.Literal[1]])
        assert is_subtype(typing.Literal[1,2,3], int)
        assert is_subtype(typing.Literal["a","b"], str)
        assert is_subtype(Tuple[typing.Literal[1,2,3], str], Tuple[int, str])

        if sys.version_info >= (3, 9):
            # the following fails for Python 3.8, because Literal[1] == Literal[True]
            #      and our caching swaps between them.
            assert is_subtype(typing.Literal[True], bool)

    @unittest.skipIf(not hasattr(typing, 'Literal'), "Literals not supported in this Python version")
    def test_context_vars(self):
        class BadEq:
            def __init__(self, smart):
                self.smart = smart

            def __eq__(self, other):
                if self.smart and cv_type_checking.get():
                    return False
                raise NotImplementedError()

        inst = BadEq(False)
        self.assertRaises(NotImplementedError, isa, inst, typing.Literal[1])

        inst = BadEq(True)
        assert isa(inst, typing.Literal[1]) == False

    def test_type_generic(self):
        assert isa(int, typing.Type)
        assert isa(int, typing.Type[int])
        assert not isa(int, typing.Type[str])
        assert isa(typing.List[int], typing.Type[typing.List[int]])
        assert not isa(typing.List[int], typing.Type[typing.List[str]])
        assert isa(int, typing.Type[object])
        assert isa(list, typing.Type[typing.Sequence])

        assert issubclass(typing.Type[int], typing.Type[int])
        assert not issubclass(typing.Type[int], typing.Type[str])
        assert issubclass(typing.Type[list], typing.Type[typing.Sequence])
        assert issubclass(typing.Type[typing.List[int]], typing.Type[typing.Sequence[int]])
        assert not issubclass(typing.Type[typing.List[int]], typing.Type[typing.Sequence[str]])

        assert issubclass(typing.Type[int], typing.Type[object])
        assert issubclass(typing.Type[int], typing.Type[typing.Any])
        assert not issubclass(typing.Type[object], typing.Type[int])
        assert issubclass(typing.Type[typing.Any], typing.Type[int])

    def test_any(self):
        assert is_subtype(int, Any)
        assert is_subtype(Any, int)
        assert is_subtype(Any, int)
        assert is_subtype(Any, Any)
        assert is_subtype(Any, Union[Any, int])
        assert is_subtype(Any, Union[Any, None])
        assert is_subtype(Union[Any, int], Any)
        assert is_subtype(Union[Any, None], Any)
        assert is_subtype(Union[Any, None], Union[Any, None])
        assert is_subtype(dict, Any, )
        assert is_subtype(Any, dict)

    def test_all(self):
        assert is_subtype(int, object)
        assert not is_subtype(object, int)
        assert is_subtype(object, object)
        assert is_subtype(object, Union[object, int])
        assert is_subtype(object, Union[object, None])
        assert is_subtype(Union[object, int], object)
        assert is_subtype(Union[object, None], object)
        assert is_subtype(Union[object, None], Union[object, None])
        assert is_subtype(dict, object, )
        assert not is_subtype(object, dict)


class TestDispatch(TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        dy = Dispatch()

        @dy
        def f(i:int):
            return i + 1

        @dy
        def f(s:str):
            return s + "1"

        try:
            @dy
            def f(x: int):
                return NotImplemented
        except ValueError:
            pass
        else:
            assert False, f

        @dy
        def g(i: int):
            return "No problem"

        assert f(1) == 2
        assert f("1") == "11"
        assert g(1) == "No problem"
        self.assertRaises(DispatchError, g, "1")


    def test_basic2(self):
        dy = Dispatch()

        @dy
        def f(i:int):
            return i

        @dy
        def f(i:int, j:int):
            return i + j

        assert f(1) == 1
        assert f(1, 1) == 2

    def test_basic3(self):
        dy = Dispatch()

        @dy
        def to_list(x:list):
            return x

        @dy
        def to_list(x:dict):
            return list(x.items())

        assert to_list([1]) == [1]
        assert to_list({1: 2}) == [(1, 2)]

    def test_with(self):
        with Dispatch() as d:
            assert isinstance(d, MultiDispatch)

    def test_ambiguity(self):
        dp = Dispatch()

        @dp
        def sum_ints(x, y):
            return None
        @dp
        def sum_ints(x: int, y):
            return x
        @dp
        def sum_ints(x, y: int):
            return y
        @dp
        def sum_ints(x: int, y: int):
            return x+y

        assert sum_ints("a", "b") == None
        assert sum_ints(27, "b") == 27
        assert sum_ints("a", 27) == 27
        assert sum_ints(13, 27) == 40


    def test_keywords(self):
        dp = Dispatch()

        @dp
        def f(x:int=2, y:int=2):
            return x-y

        assert f(5, 1) == 4
        assert f(4) == 2
        assert f() == 0

        @dp
        def f(x:object, y:int=2):
            return x+y

        assert f(5, 1) == 4
        assert f(4) == 2
        assert f() == 0
        assert f(1.5) == 3.5
        assert f(1.5, 1) == 2.5

    def test_methods(self):
        dy = Dispatch()

        class A:
            @dy
            def f(self, i:int):
                return i

            @dy
            def f(self, i:int, j:int):
                return i + j

        a = A()
        assert a.f(1) == 1
        assert a.f(1, 1) == 2

    def test_init(self):
        dy = Dispatch()

        class A:
            @dy
            def __init__(self, i:int):
                self.x = i

            @dy
            def __init__(self, i:int, j:int):
                self.x = i + j

        assert A(1).x == 1
        assert A(1, 1).x == 2


    def test_one_shadow(self):
        dy = Dispatch()

        @dy
        def f(i:int):
            return i + 1

        @dy
        def f(i:object):
            return i

        assert f(1) == 2
        assert f("a") == "a"


        @dy
        def f(a, i:int, b, s:str):
            return i + 1

        @dy
        def f(a, i:object, b, s:object):
            return i

        assert f(0, 1, 0, "a") == 2
        assert f(0, 1, 0, 4) == 1
        assert f(0, "z", 0, "z") == "z"

        @dy
        def g(a, i:int, b, s:object):
            return i + 1

        @dy
        def g(a, i:object, b, s:str):
            return i

        self.assertRaises(DispatchError, g, 0,1,0,"a")
        self.assertRaises(DispatchError, g, 0,"z",0,3)


    def test_two_shadows(self):
        dy = Dispatch()

        class test_int(int):
            pass

        assert issubclass(test_int, int)
        assert not issubclass(int, test_int)

        @dy
        def f(i:int):
            return int

        @dy
        def f(i:object):
            return object

        @dy
        def f(i:test_int):
            return test_int

        assert f(3) == int
        assert f("a") == object
        assert f(test_int(4)) == test_int

        @dy
        def f(i:int, j:test_int, k:int):
            return int

        @dy
        def f(i:object, j:object, k:int):
            return object

        @dy
        def f(i:test_int, j:test_int, k:test_int):
            return test_int

        assert f(3, test_int(2), 3) == int
        assert f("a", "b", 5) == object
        assert f(test_int(4), test_int(2), test_int(4)) == test_int
        assert f(test_int(4), test_int(2), 4) == int
        assert f(4, test_int(2), test_int(4)) == int
        assert f(4, "a", test_int(4)) == object
        assert f(test_int(4), "a", test_int(4)) == object

        @dy
        def f(i:int, j:object, k:object):
            return "Oops"

        self.assertRaises(DispatchError, f, 1, 2, 3)
        self.assertRaises(DispatchError, f, 4 ,"b", 4)
        assert f(test_int(4), test_int(2), test_int(4)) == test_int
        assert f("b", "a", test_int(4)) == object
        assert f(3, "a", "b") == "Oops"


        try:
            @dy
            def f(i:int, j:object, k:object):
                return "Oops"
        except ValueError:
            pass
        else:
            assert False


    def test_canonical_types(self):
        def _test_canon(*types, include_none=False):
            dp = Dispatch()

            # for t1 in types:
            #     for t2 in types:
            #         assert issubclass(t1, t2), (t1, t2)

            @dp
            def f(x: types[0]):
                pass

            if include_none:
                try:
                    @dp
                    def f(x):
                        pass
                    assert False
                except ValueError:
                    pass

            for t in types[1:]:
                try:
                    @dp
                    def f(x: t):
                        pass
                    assert False, t
                except ValueError:
                    pass

        _test_canon(object, Union[object], include_none=True)
        # XXX the Any test should fail, but atm we only throw the error on lookup
        # _test_canon(Any, Union[Any], include_none=True)
        _test_canon(list, List, List[Any], Union[List[Union[Any]]])
        _test_canon(tuple, Tuple)
        _test_canon(dict, Dict, Dict[Any, Any])
        _test_canon(int, Union[int])
        _test_canon(int, Union[Union[int]])

    def test_union(self):
        dp = Dispatch()

        @dp
        def f(x: Union[int, str]):
            return True

        @dp
        def f(x):
            return False

        assert f(4)
        assert f("a")
        assert not f(())


        @dp
        def g(x: Optional[str]):
            return 0

        assert g("a") == 0
        assert g(None) == 0

        @dp
        def h(x: Optional[str]):
            return 0

        @dp
        def h(x: Optional[int]):
            return 1

        assert h("a") == 0
        assert h(2) == 1
        self.assertRaises(DispatchError, h, None)


    def test_union2(self):
        assert issubclass(int, Union[int, str])
        assert issubclass(Union[int, str], Union[int, str])
        assert issubclass(Union[int, str], Union[int, str, dict])
        assert not issubclass(Union[int, str, dict], Union[int, str])
        assert issubclass(int, (str, int))

        dp = Dispatch()

        @dp
        def f(x: Union[int, str]):
            return Union

        @dp
        def f(x: Union[int, str, dict]):
            return dict

        @dp
        def f(x: int):
            return int

        @dp
        def f(x):
            return object

        assert f("a") is Union
        assert f(3) is int
        assert f([]) is object
        assert f({}) is dict

    def test_init(self):
        dp = Dispatch()

        @dataclass(frozen=False)
        class Point:
            x: int = 0
            y: int = 0
            
            @dp
            def __init__(self, points: list):
                self.x, self.y = points
            
        assert Point() == Point([0, 0])

        p1 = Point(10, 20)
        p2 = Point([10, 20])
        assert p1 == p2

    @unittest.skip("not implemented yet")
    def test_type_generic(self):
        dp = Dispatch()

        @dp
        def f(t: typing.Type[int]):
            return "int"

        @dp
        def f(t: typing.Type[str]):
            return "str"

        assert f(int) == "int"
        assert f(str) == "str"

    def test_sequence(self):
        pass

    def test_mapping(self):
        pass

    def test_iterator(self):
        pass

    def test_callable(self):
        pass

    def test_match(self):
        pass

    def test_dispatch_singleton(self):
        def f(a: int):
            return 'a'
        f.__module__ = 'a'
        f1 = multidispatch(f)

        def f(a: int):
            return 'a'
        f.__module__ = 'b'
        f2 = multidispatch(f)

        assert f1(1) == 'a'
        assert f2(1) == 'a'

        def f(a: int):
            return 'a'
        f.__module__ = 'a'
        self.assertRaises(ValueError, multidispatch, f)

    def test_none(self):
        dp = Dispatch()

        @dp
        def f(t: None):
            return "none"

        @dp
        def f(t: int):
            return "int"

        assert f(2) == "int"
        assert f(None) == "none"

    def test_qualified_name(self):
        md = Dispatch()

        class A:
            @md
            def a(self, points: list):
                ...

        class B:
            @md
            def a(self, points: list):
                ...

    def test_generic(self):
        _Leaf_T = TypeVar("_Leaf_T")
        class Tree(Generic[_Leaf_T]):
            pass

        @multidispatch
        def f(t: Tree[int]):
            pass

        f(Tree())

    def test_literal_dispatch(self):
        try:
            @multidispatch
            def f(x: typing.Literal[1]):
                return 1

            @multidispatch
            def f(x: typing.Literal[2]):
                return 2
        except ValueError:
            pass
        else:
            assert False

        # If it was working..
        # assert f(1) == 1
        # assert f(2) == 2


class TestDataclass(TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        @dataclass
        class Point:
            x: int
            y: int

            def __post_init__(self):
                assert self.x != 0

        p = Point(2,3)
        assert p.asdict() == {'x':2, 'y':3}

        p2 = p.replace(x=30)
        # assert dict(p2) == {'x':30, 'y':3}
        assert p2.aslist() == [30, 3]
        assert p2.astuple() == (30, 3)

        assert p2.asdict() == {'x':30, 'y':3}
        assert list(p2.asdict().keys()) == ['x', 'y'] # test order

        self.assertRaises(AssertionError, Point, 0, 2)

        self.assertRaises(TypeError, Point, 0, "a") # Before post_init
        self.assertRaises(TypeError, Point, 1.2, 3)

    def test_typing(self):
        @dataclass
        class A:
            a: List[int]
            b: Optional[str]

        a = A([1,2,3], "a")
        a = A([], None)

        try:
            a.b = "str"
            assert False
        except FrozenInstanceError:
            pass

        self.assertRaises(TypeError, A, [1,2,"a"], None)
        self.assertRaises(TypeError, A, [1,2,3], 3)
        self.assertRaises(TypeError, A, None, None)

        @dataclass
        class B:
            a: Tuple
            b: FrozenSet
            i: Iterable

        b = B((1,2), frozenset({3}), iter([]))

        @dataclass
        class C:
            a: String
            b: String(max_length=4)

        C("hello", "a")
        self.assertRaises(TypeError, C, 3)
        self.assertRaises(TypeError, C, "hello", "abcdef")

        @dataclass
        class P:
            a: Int(min=0) = None

        assert P(10).a == 10
        assert P(0).a == 0
        assert P().a == None
        self.assertRaises(TypeError, P, -3)

    def test_typing_optional(self):
        @dataclass
        class A:
            a: list = None

        A([1,2])
        A()
        A(None)
        self.assertRaises(TypeError, A, 'a')

        @dataclass(frozen=False)
        class A:
            a: list = None

        A([1,2])
        A()
        A(None)
        self.assertRaises(TypeError, A, 'a')

        @dataclass
        class B:
            b: Optional[list] = None

        B([1,2])
        B()
        B(None)
        self.assertRaises(TypeError, B, 'a')

        @dataclass
        class C:
            a: Optional[list]

        C([1,2])
        C(None)
        self.assertRaises(TypeError, C)
        self.assertRaises(TypeError, C, 'a')


        @dataclass(check_types='cast')
        class D:
            a: Optional[A]

        D(A())
        D({'a': [1,2]})
        D({'a': None})
        self.assertRaises(TypeError, D, {'b': [1,2]})
        self.assertRaises(TypeError, D)

        @dataclass(check_types='cast')
        class E:
            a: Union[A, B] = None

        E()
        E({'a': [1,2]})
        E({'b': [1,2]})
        self.assertRaises(TypeError, D, {'c': [1,2]})

        @dataclass
        class F:
            a: String = None
            b: String(max_length=4) = None

        F("hello", "a")
        self.assertRaises(TypeError, C, 3)
        self.assertRaises(TypeError, C, "hello", "abcdef")

    def test_typing_optional2(self):
        assert is_subtype(List[str], Optional[Union[List[str], int]])

    def test_required_keyword(self):
        @dataclass
        class A:
            a: int = None
            b: int

        assert A(b=10) == A(None, 10)
        self.assertRaises(TypeError, A)
        self.assertRaises(TypeError, A, 2)

    def test_required_keyword2(self):
        @dataclass(check_types=False)   # Alternate behavior
        class A:
            a: int = 4
            b: int

        assert A(b=10) == A(4, 10)
        self.assertRaises(TypeError, A)
        self.assertRaises(TypeError, A, 2)

    def test_self_reference(self):
        @dataclass
        class A:
            items: List["A"]

        a1 = A([])
        a2 = A([a1])
        self.assertRaises(TypeError, A, [1])

    def test_forward_references(self):
        @dataclass
        class A:
            i: 'int'
            b: 'B'
            l: 'List[int]'

        class B:
            pass

        A(10, B(), [3])
        self.assertRaises(TypeError, A, 2, 3, [])
        self.assertRaises(TypeError, A, 'a', B(), [])
        self.assertRaises(TypeError, A, 10, B(), ['a'])

        @dataclass
        class Tree:
            data: Any
            children: List['Tree']
        
        t = Tree('a', [])
        t = Tree('a', [t])
        self.assertRaises(TypeError, Tree, 'a', [1])

    def test_forward_reference_cache(self):
        @dataclass
        class A:
            b: 'B'

        class B:
            pass

        a = A(B())
        self.assertRaises(TypeError, A, 1)

        @dataclass
        class A:
            b: 'B'

        class B:
            pass

        a = A(B())
        self.assertRaises(TypeError, A, 1)

    def test_unfrozen(self):
        @dataclass(frozen=False, slots=False)
        class A:
            a: str

        a = A("hello")
        a.a = "ba"
        a.b = 4 # New attributes aren't tested
        try:
            a.a = 4
        except TypeError:
            pass
        else:
            assert False

    def test_unfrozen2(self):
        @dataclass(frozen=False)
        class A:
            a: list = None

        a = A([1,2])
        assert a.a == [1,2]
        a.a = None
        assert a.a is None

    def test_frozen(self):
        @dataclass
        class A:
            a: str

        a = A("a")
        b = A("a")
        x = A("c")
        assert a == b
        assert hash(a) == hash(b)
        assert a != x

    def test_slots(self):
        @dataclass(frozen=False, slots=True)
        class A:
            a: str

        a = A("hello")
        a.a = "ba"
        try:
            a.b = "hello"
        except AttributeError:
            pass
        else:
            assert False

        @dataclass(frozen=True, slots=True)
        class A:
            a: str

        assert A.__slots__ == ('a',)

        a = A("hello")
        try:
            a.a = "ba"
        except FrozenInstanceError:
            pass
        else:
            assert False

    def test_custom_isinstance(self):
        class EnsureContains(Configuration):
            def ensure_isa(self, item, container, sampler=None):
                if item not in container:
                    raise TypeError(item)

            def cast(self, obj, t):
                raise NotImplementedError()

        @dataclass(config=EnsureContains())
        class A:
            a: range(10)
            b: ("a", "b")

        a = A(3, "a")
        a = A(9, "b")
        self.assertRaises(TypeError, A, 11, "a")
        self.assertRaises(TypeError, A, 3, "c")

    def test_check_types(self):
        @dataclass(frozen=False, check_types=False)
        class A:
            a: str

        a = A(6)
        a.a = 4


    def test_default_mutables(self):
        @dataclass
        class A:
            a: List = []
            b: Dict = {}
            c: Set = {1}

        a = A()
        assert a.a == []
        assert a.b == {}

        assert a.a is not A().a

        assert a.c == {1}
        assert a.c is not A().c

    def test_iter(self):
        @dataclass
        class A:
            a: iter

        a = A(iter([1,2,3]))
        assert list(a.a) == [1,2,3]

    def test_sample(self):
        @dataclass(check_types='sample')
        class A:
            a: List[int]


        nums = list(range(1000))
        a = A( nums )

        self.assertRaises(TypeError, A, ['1', '2'] )

    def test_field1(self):
        @dataclass
        class A:
            a: str
            b: List = field(compare=False, repr=False, hash=False)

        a = A("hi", [1])
        assert a.a == "hi"
        assert a.b == [1]

        assert a == A("hi", [2])

    def test_field2(self):
        @dataclass
        class A:
            a: dict
            b: Dict[str, int] = field(default_factory=dict)

        a = A({})
        assert a.a == {}
        assert a.b == {}

    def test_field3(self):
        @dataclass
        class A:
            a: List = field(default=[])

        a = A()
        assert a.a == []
        assert a.a is not A().a

    def test_field_auto_optional(self):
        @dataclass
        class A:
            a: int = field(default=None)

        assert A().a is None
        assert A(None).a is None
        assert A(1).a == 1



    def test_json_serialize(self):
        @dataclass
        class Bar:
            baz: int

        @dataclass
        class Foo:
            bars: List[Bar]
            d: Dict[str, Bar]

        assert Foo(
            [Bar(0)],
            {"a": Bar(2)}
            ).json() == {
                "bars": [{"baz": 0}],
                "d": {"a": {"baz": 2}}
                }

    def test_update_options(self):
        no_eq = dataclass(eq=False, check_types=True)

        @no_eq
        class A:
            a: int = None

        assert A() != A()
        self.assertRaises(TypeError, A, "a")

        @no_eq(eq=True)
        class B:
            a: int = None

        assert B() == B()
        self.assertRaises(TypeError, B, "a")

        @no_eq(check_types=False)
        class C:
            a: int = None

        assert C() != C()
        assert C("a").a == "a"

if __name__ == '__main__':
    unittest.main()
