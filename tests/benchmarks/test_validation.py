import datetime
import typing as t
import pytest

from runtype import isa, issubclass
from beartype.door import is_bearable

STDLIB = ("stdlib (isinstance)", isinstance)
RUNTYPE = ("runtype (isa)", isa)
BEARTYPE = ("beartype (is_bearable)", is_bearable)
each_isa = pytest.mark.parametrize(
    "libname,tester", [STDLIB, RUNTYPE, BEARTYPE]
)
each_isa_ext = pytest.mark.parametrize(
    "libname,tester", [RUNTYPE, BEARTYPE]
)


# @each_isa
# @pytest.mark.benchmark
# def test_isa_int(benchmark, tester):
#     res = benchmark(tester, 1, int)
#     assert res == True


def _test_isa_tuple(tester):
    types = (int, str, float, bool)
    res = (
        tester(1, types),
        tester("a", types),
        not tester(None, types),
    )
    return all(res)


@each_isa
@pytest.mark.benchmark(group="isinstance(x, (int, str, float, bool)) $$ div:3")
def test_isa_tuple(benchmark, libname, tester):
    res = benchmark(_test_isa_tuple, tester)
    assert res == True


@each_isa_ext
@pytest.mark.benchmark(group="isinstance(x, list[int])")
def test_isa_generic(benchmark, libname, tester):
    res = benchmark(tester, [1], list[int])
    assert res == True


# @each_isa_ext
# @pytest.mark.benchmark
# def test_isa_generic2(benchmark, tester):
#     # https://github.com/beartype/beartype/issues/246
#     res = benchmark(tester, {"a": 2}, dict[str, int])
#     assert res == True


def _test_isa_union(tester):
    u = t.Union[int, str, float, bool]
    res = (
        tester(1, u),
        tester("a", u),
        not tester(None, u),
    )
    return all(res)


@each_isa
@pytest.mark.benchmark(group="isinstance(x, int | str | float | bool) $$ div:3")
def test_isa_union(benchmark, libname, tester):
    res = benchmark(_test_isa_union, tester)
    assert res == True
