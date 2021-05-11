import unittest
from unittest import TestCase

from runtype.pytypes import List, Dict, Any, OneOf


class TestTypes(TestCase):
    def test_basic(self):
        assert List + Dict == Dict + List
        assert Any + ((Any + Any) + Any) is Any

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


if __name__ == '__main__':
    unittest.main()