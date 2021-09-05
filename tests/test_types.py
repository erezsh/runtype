import unittest
from unittest import TestCase

from runtype.pytypes import List, Dict, Int, Any
from runtype.typesystem import TypeSystem


class TestTypes(TestCase):
    def test_basic(self):
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




if __name__ == '__main__':
    unittest.main()