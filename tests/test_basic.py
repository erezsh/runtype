import unittest
from unittest import TestCase
from collections import abc
import sys

import typing
from typing import Any, List, Dict, Tuple, Union, Optional, Callable, Set, FrozenSet
from collections.abc import Iterable
from dataclasses import FrozenInstanceError

import logging
logging.basicConfig(level=logging.INFO)

from runtype import Dispatch, DispatchError, dataclass, isa, issubclass, assert_isa, String
from runtype.dataclass import Configuration


class TestIsa(TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        assert isa(1, int)
        assert issubclass(int, object)
        assert isa([1,2], List[int])
        assert not isa([1,"a"], List[int])
        assert not isa([1,2], List[str])
        assert isa(1, (int, str))
        assert not isa(1, (float, str))

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

        assert issubclass(List[int], list)
        assert issubclass(Tuple[int], tuple)
        assert issubclass(Tuple[int, int], tuple)
        assert not issubclass(tuple, Tuple[int])

        assert isa((3,), Tuple[int])
        assert isa((3, 5), Tuple[int, int])
        assert not isa((3, 5), Tuple[int, float])
        assert not isa((3, 5), Tuple[int])

        assert isa((3,), (Tuple[int], list))

        assert issubclass(Any, Any)
        assert not issubclass(Any, int)
        assert issubclass(List[int], Any)


        # Mappings
        assert issubclass(dict, abc.Mapping)
        assert issubclass(dict, typing.Mapping)
        assert isa({'a': 'b'}, typing.Mapping)
        assert isa({'a': 'b'}, typing.Mapping)

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

    def test_assert(self):
        assert_isa(1, int)
        assert_isa("a", str)
        self.assertRaises(TypeError, assert_isa, 1, str)
        assert_isa([1,2], List[int])
        self.assertRaises(TypeError, assert_isa, [1,"2"], List[int])


    @unittest.skipIf(sys.version_info < (3, 8), "Not supported before Python 3.8")
    def test_py38(self):
        assert isa('a', typing.Literal['a', 'b'])
        assert not isa('c', typing.Literal['a', 'b'])


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


    def test_canonization(self):
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

        _test_canon(object, Any, Union[Any], include_none=True)
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
        assert dict(p) == {'x':2, 'y':3}

        p2 = p.replace(x=30)
        assert dict(p2) == {'x':30, 'y':3}
        assert p2.aslist() == [30, 3]
        assert p2.astuple() == (30, 3)

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

    def test_typing_optional(self):
        @dataclass
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



    def test_unfrozen(self):
        @dataclass(frozen=False)
        class A:
            a: str

        a = A("hello")
        a.a = "ba"
        a.b = 4 # New attributes aren't tested
        try:
            a.a = 4
        except TypeError:
            pass

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

    def test_custom_isinstance(self):
        class EnsureContains(Configuration):
            def ensure_isa(self, item, container):
                if item not in container:
                    raise TypeError(item)

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

    def test_cast_dict(self):
        @dataclass
        class Point:
            x: float
            y: float

        @dataclass(check_types='cast')
        class Rect:
            start: Point
            end: Point

        start = {'x': 10.0, 'y': 10.0}
        end = {'x': 3.14, 'y': 234.3}
        rect = {'start': start, 'end': end}

        r = Rect(**rect)
        assert r.json() == rect, (dict(r), rect)

        self.assertRaises(TypeError, Rect, start={'x': 10.0, 'y': 10.0, 'z': 42.2}, end=end)
        self.assertRaises(TypeError, Rect, start={'x': 10.0}, end=end)

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





if __name__ == '__main__':
    unittest.main()
