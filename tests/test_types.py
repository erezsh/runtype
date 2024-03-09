import sys
import unittest
from unittest import TestCase
import typing
import collections.abc as cabc
import io

from runtype.base_types import DataType, GenericType, PhantomType, Variance
from runtype.pytypes import type_caster, List, Dict, Int, Any, Constraint, String, Tuple, Iter, Literal, NoneType, Sequence, Mapping    
from runtype.typesystem import TypeSystem

make_type = type_caster.to_canon

class TestTypes(TestCase):
    def test_basic_types(self):
        Int = DataType()
        Str = DataType()
        Array = GenericType(DataType(), Any, Variance.Covariant)

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

        assert P[Q] <= Q
        assert P[Q] <= P
        assert not P <= Q[Int]

        assert P[Q[Int]] <= P
        assert P[Q[Int]] <= Q
        assert P[Q[Int]] <= Int
        assert P[Q[Int]] <= P[Q]
        assert P[Q[Int]] <= P[Int]
        assert P[Q[Int]] <= Q[Int]
        assert P[Q[Int]] <= P[Q[Int]]
        assert Int <= P[Q[Int]]

        assert P <= P + Int
        assert not P <= Dict
        assert not P <= Int + Dict


    def test_pytypes1(self):
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
        int_pair = Constraint(typing.Sequence[int], [lambda a: len(a) == 2])
        assert int_pair.test_instance([1,2])
        assert not int_pair.test_instance([1,2,3])
        assert not int_pair.test_instance([1,'a'])

        assert String.test_instance('a')
        assert not String.test_instance(3)

        assert String(max_length=5).test_instance('abc')
        assert String(min_length=2).test_instance('abc')
        assert not String(max_length=5).test_instance('abcdef')
        assert not String(min_length=5).test_instance('abc')

        i = Int(min=10, max=12)
        assert i.test_instance(11)
        assert not i.test_instance(9)
        assert not i.test_instance(13)

        assert int_pair == int_pair
        assert int_pair <= int_pair
        assert int_pair >= int_pair
        assert int_pair <= Any
        assert Any >= int_pair
        assert not int_pair <= Dict
        assert not int_pair <= Int
        assert not int_pair <= Int + Dict
        assert not int_pair <= Tuple

        assert int_pair <= Sequence
        assert Sequence >= int_pair
        assert int_pair <= Sequence[Int]
        assert Sequence[Int] >= int_pair
        assert not int_pair <= Sequence[String]
        assert not Sequence[String] >= int_pair



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

    def test_pytypes2(self):
        assert Tuple <= Tuple
        assert Tuple >= Tuple
        # assert Tuple[int] <= Tuple
        assert not List <= Tuple
        assert not Tuple <= List
        assert not Tuple <= Int
        assert not Int <= Tuple

        one = Literal([1])
        one_two = Literal([1, 2])
        one_three = Literal([1, 3])
        assert one <= one_two
        assert not one_three <= one_two
        assert one_three >= one
        assert not Literal([1]) <= Tuple
        assert not Literal([1]) >= Tuple
        assert not Tuple <= Literal([1])

        Tuple.validate_instance((1, 2))
        self.assertRaises(TypeError, Tuple.validate_instance, 1)

        assert List[int] == List[int]

        self.assertRaises(TypeError, lambda: Tuple >= 1)
        self.assertRaises(TypeError, lambda: Literal >= 1)

        assert type_caster.to_canon(typing.List[int]).cast_from([]) == []
        assert type_caster.to_canon(typing.List[int]).cast_from(()) == []
        assert type_caster.to_canon(typing.Dict[int, int]).cast_from({}) == {}
        assert type_caster.to_canon(typing.Dict[int, int]).cast_from([]) == {}

        tpl0 = type_caster.to_canon(typing.Tuple)
        tpl1 = type_caster.to_canon(typing.Tuple[int])
        tpl2 = type_caster.to_canon(typing.Tuple[int, ...])
        tpl0b = type_caster.to_canon(tuple)
        tpl3 = type_caster.to_canon(typing.Tuple[typing.Union[int, str]])
        tpl4 = type_caster.to_canon(typing.Tuple[typing.Union[int, str], ...])
        assert tpl0 is tpl0b
        assert tpl1 <= tpl0
        assert tpl2 <= tpl0

        assert tpl3 <= tpl0
        assert tpl1 <= tpl3
        assert not tpl3 <= tpl1
        assert not tpl0 <= tpl3

        assert tpl2 <= tpl4

        assert tpl2.test_instance((1,2,3))
        assert not tpl2.test_instance((1,2,3, 'a'))
        if sys.version_info >= (3, 11):
            self.assertRaises(ValueError, type_caster.to_canon, typing.Tuple[...])
            self.assertRaises(ValueError, type_caster.to_canon, typing.Tuple[int, str, ...])


    def test_pytypes3(self):
        assert Any + Int == Any
        assert Int + Any == Any


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

    def test_any(self):
        assert Any <= Any
        assert Any <= Any + Int
        assert Any <= Any + NoneType
        assert Any + Int <= Any
        assert Any + NoneType <= Any

    def test_invariance(self):
        assert List <= Sequence
        assert not List[List] <= List[Sequence]
        assert not List[Sequence] <= List[List] 

        assert Dict <= Mapping
        assert Dict[Int, Int] <= Mapping[Int, Int]
        assert Mapping[Int, List] <= Mapping[Int, Sequence]
        assert not Dict[Int, List] <= Dict[Int, Sequence]
        assert not Mapping[Int, Sequence] <= Mapping[Int, List]
        assert not Dict[Int, Sequence] <= Dict[Int, List]

    def test_callable(self):
        repeat = make_type(typing.Callable[[str, int], str])
        class _Str(str):
            pass
        assert repeat <= repeat
        assert not make_type(typing.Callable[[_Str, int], str]) <= repeat
        assert not make_type(typing.Callable[[int, str], str]) <= repeat
        assert not repeat <= make_type(typing.Callable[[str, int], _Str])
        assert make_type(typing.Callable[[str, int], _Str]) <= repeat
        assert repeat <= make_type(typing.Callable[[_Str, int], str])

    def test_io(self):
        IO = make_type(io.IOBase)
        TextIO = make_type(io.TextIOBase)
        assert IO <= IO
        assert TextIO <= IO
        assert IO.test_instance(sys.stdout)

    def test_typing_io(self):
        IO = make_type(typing.IO)
        TextIO = make_type(typing.TextIO)
        assert IO <= IO
        assert TextIO <= IO
        assert IO.test_instance(sys.stdout)



if __name__ == '__main__':
    unittest.main()