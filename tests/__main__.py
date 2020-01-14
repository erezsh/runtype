import unittest
from unittest import TestCase

from typing import Any, List, Dict, Tuple, Union, Optional, Callable
from dataclasses import FrozenInstanceError

import logging
logging.basicConfig(level=logging.INFO)

from runtype import Dispatch, DispatchError, dataclass, isa, issubclass

class TestIsa(TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        assert isa(1, int)
        assert issubclass(int, object)
        assert isa([1,2], List[int])
        assert not isa([1,"a"], List[int])
        assert not isa([1,2], List[str])

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

    def test_unfrozen(self):
        @dataclass(frozen=False)
        class A:
            a: str

        a = A("hello")
        a.a = "ba"
        a.a = 4     # Bad, but that's how it is

    def test_custom_isinstance(self):
        @dataclass(isinstance=lambda x,y: x in y)
        class A:
            a: range(10)
            b: ("a", "b")

        a = A(3, "a")
        a = A(9, "b")
        self.assertRaises(TypeError, A, 11, "a")
        self.assertRaises(TypeError, A, 3, "c")


if __name__ == '__main__':
    unittest.main()
