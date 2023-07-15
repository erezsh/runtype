import unittest
from unittest import TestCase
import typing
import collections.abc as cabc

from runtype.base_types import DataType, ContainerType, PhantomType
from runtype.pytypes import type_caster, List, Dict, Int, Any, Constraint, String, Tuple, Iter, Literal
from runtype.typesystem import TypeSystem


class TestTypes(TestCase):
    def test_basic_types(self):
        Int = DataType()
        Str = DataType()
        Array = ContainerType()

        assert Int == Int
        assert Int != Str
        assert Int != Array
        assert Int <= Any
        assert Array <= Any

        assert Array[Any] == Array
        assert Array[Int] <= Array[Any]

        array = Array[Array]
        assert array[Array[Array]] <= array

        self.assertRaises(TypeError, lambda: Int[Str])
        self.assertRaises(TypeError, lambda: (Array[Array])[Int])

        assert Int <= Int + Array
        assert Int * Array == Int * Array

    def test_phantom(self):
        Int = DataType()
        P = PhantomType()
        Q = PhantomType()

        assert P == P
        assert P <= P
        assert P != Q
        assert not P <= Q
        assert not Q <= P


        assert Int <= P[Int]
        assert P[Int] <= Int
        assert P[Int] <= P[Int]

        assert P[Int] <= P
        assert not P <= P[Int]
        assert Q[P] <= Q

        assert P[Q[Int]] <= P[Q]
        assert P[Q[Int]] <= P[Int]
        assert P[Q[Int]] <= Q[Int]
        assert P[Q[Int]] <= Int



    def test_pytypes(self):
        assert List + Dict == Dict + List
        assert Any + ((Any + Any) + Any) is Any

        assert (List+Dict) + Int == List + (Dict+Int)
        assert (List+Dict) != 1
        assert List + List == List

        self.assertRaises(TypeError, lambda: 1 <= List)
        self.assertRaises(TypeError, lambda: 1 >= List)
        self.assertRaises(TypeError, lambda: 1 >= Any)
        self.assertRaises(TypeError, lambda: 1 <= Any)
        self.assertRaises(TypeError, lambda: 1 <= List+Dict)
        self.assertRaises(TypeError, lambda: 1 >= List+Dict)
        self.assertRaises(TypeError, lambda: 1 <= List*Dict)
        self.assertRaises(TypeError, lambda: 1 >= List*Dict)

        assert List[int] == List[int]
        assert List[int] != List[str]
        assert Dict == Dict[Any*Any]

        assert repr(List[int]) == repr(List[int])
        assert repr(Any) == 'Any'

        assert List <= List + Dict
        assert List + Dict >= List

        assert {List+Dict: True}[Dict+List]		# test hashing

        assert Dict*List <= Dict*List

        assert ((Int * Dict) * List) == (Int * (Dict * List))

        assert List[Any] == List

    def test_constraint(self):
        int_pair = Constraint(typing.List[int], [lambda a: len(a) == 2])
        assert int_pair.test_instance([1,2])
        assert not int_pair.test_instance([1,2,3])
        assert not int_pair.test_instance([1,'a'])

        assert String.test_instance('a')
        assert not String.test_instance(3)

        assert String(max_length=5).test_instance('abc')
        assert not String(max_length=5).test_instance('abcdef')



    def test_typesystem(self):
        t = TypeSystem()
        o = object()
        assert t.canonize_type(o) is o

        class IntOrder(TypeSystem):
            def issubclass(self, a, b):
                return a <= b 

            def get_type(self, a):
                return a

        i = IntOrder()
        assert i.isinstance(3, 3)
        assert i.isinstance(3, 4)
        assert not i.isinstance(4, 3)

    def test_pytypes(self):
        assert Tuple <= Tuple
        assert Tuple >= Tuple
        # assert Tuple[int] <= Tuple
        assert not List <= Tuple
        assert not Tuple <= List
        assert not Tuple <= Int
        assert not Int <= Tuple

        assert Literal([1]) <= Literal([1, 2])
        assert not Literal([1, 3]) <= Literal([1, 2])
        assert not Literal([1]) <= Tuple
        assert not Literal(1) >= Tuple
        assert not Tuple <= Literal(1)

        Tuple.validate_instance((1, 2))
        self.assertRaises(TypeError, Tuple.validate_instance, 1)

        assert List[int] == List[int]

        self.assertRaises(TypeError, lambda: Tuple >= 1)
        self.assertRaises(TypeError, lambda: Literal >= 1)

        type_caster.to_canon(list[int]).cast_from([])
        type_caster.to_canon(list[int]).cast_from(())



    def test_canonize_pytypes(self):
        pytypes = [
            int, str, list, dict, typing.Optional[int],
            typing.Sequence[int],

            # collections.abc
            cabc.Hashable, cabc.Sized, cabc.Callable, cabc.Iterable, cabc.Container,
            cabc.Collection, cabc.Iterator, cabc.Reversible, cabc.Generator,
            cabc.Sequence, cabc.MutableSequence, cabc.ByteString,
            cabc.Set, cabc.MutableSet,
            cabc.Mapping, cabc.MutableMapping,
            cabc.MappingView, cabc.ItemsView, cabc.KeysView, cabc.ValuesView,
            cabc.Awaitable, cabc.Coroutine, 
            cabc.AsyncIterable, cabc.AsyncIterator, cabc.AsyncGenerator,

            typing.NoReturn
        ]
        for t in pytypes:
            a = type_caster.to_canon(t)
            # assert a.kernel == t, (a,t)


        type_to_values = {
            cabc.Hashable: ([1, "a", frozenset()], [{}, set()]),
            cabc.Sized: ([(), {}], [10]),
            cabc.Callable: ([int, lambda:1], [3, "a"]),
            cabc.Iterable: ([(), {}, "", iter([])], [3]),
            cabc.Container: ([(), ""], [3]),
            cabc.Collection: ([(), ""], [iter([])]),
            cabc.Iterator: ([iter([])], [[]]),
            cabc.Reversible: ([[], ""], [iter([])]),
            cabc.Generator: ([(x for x in [])], [3, iter('')]),

            cabc.Set: ([set()], [{}]),
            cabc.ItemsView: ([{}.items()], [{}])
        }

        for pyt, (good, bad) in type_to_values.items():
            t = type_caster.to_canon(pyt)
            for g in good:
                assert t.test_instance(g), (t, g)
            for b in bad:
                assert not t.test_instance(b), (t, b)






if __name__ == '__main__':
    unittest.main()