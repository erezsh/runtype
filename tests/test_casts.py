from datetime import datetime
from unittest import TestCase
from typing import List, Dict

from runtype import dataclass, String, Int, Dispatch

class TestCasts(TestCase):

    def test_typing_cast(self):

        @dataclass(check_types='cast')
        class P:
            a: Int(min=0) = None

        assert P(10)
        assert P(10).a == 10
        assert P(0).a == 0
        assert P().a == None
        self.assertRaises(TypeError, P, -3)

        assert P('10').a == 10
        assert P('0').a == 0
        assert P('+3').a == 3
        self.assertRaises(TypeError, P, '-3')


    def test_dates(self):
        @dataclass(check_types='cast')
        class A:
            a: datetime

        d = datetime.now()
        assert A(d).a.toordinal() == d.toordinal()
        assert A(d.isoformat()).a.toordinal() == d.toordinal()
        self.assertRaises(TypeError, A, 'bla')


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

        @dataclass(check_types='cast')
        class A:
            a: dict
            b: Dict[float, String] = None

        A({})
        A({1: 2})
        A({1: 2}, {1.1: 'a'})
        A({1: 2}, {1: 'a'})
        A({1: 2}, None)
        self.assertRaises(TypeError, A, [1])
        self.assertRaises(TypeError, A, {}, {'b': 'c'})
        self.assertRaises(TypeError, A, {}, {3: 2})

    def test_cast_generic(self):
        @dataclass(check_types='cast')
        class Point:
            x: float
            y: float

        @dataclass(check_types='cast')
        class Polygon:
            points: List[Point]

        p1 = {'x': 1, 'y': 2}
        p2 = {'x': 2, 'y': 3}
        Polygon([p1, p2])

    def test_custom_casts(self):
        @dataclass
        class Name:
            first: str
            last: str = None

            @classmethod
            def cast_from(cls, s: str):
                return cls(*s.split())

        @dataclass(check_types='cast')
        class Person:
            name: Name

        p = Person("Albert Einstein")
        assert p.name.first == 'Albert'
        assert p.name.last == 'Einstein'

        p = Person("Dodo")
        assert p.name.first == 'Dodo'
        assert p.name.last == None


    def test_custom_casts2(self):
        dp = Dispatch()

        @dataclass
        class Name:
            first: str
            last: str = None

            @classmethod
            @dp
            def cast_from(cls, s: str):
                return cls(*s.split())

            @classmethod
            @dp
            def cast_from(cls, s: (tuple, list)):
                return cls(*s)

        @dataclass(check_types='cast')
        class Person:
            name: Name
            bla: int = None

        assert Person("Albert Einstein") == Person(('Albert', 'Einstein'), None) == Person(['Albert', 'Einstein'])
