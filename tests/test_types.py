import unittest
from unittest import TestCase

from runtype.pytypes import List, Dict


class TestTypes(TestCase):
    def test_basic(self):
        assert List + Dict == Dict + List

        self.assertRaises(TypeError, lambda: 1 <= List)
        self.assertRaises(TypeError, lambda: 1 >= List)

if __name__ == '__main__':
    unittest.main()