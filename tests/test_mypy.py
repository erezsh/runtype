from pathlib import Path

import pytest

# mypy ships no pypy wheels (it's mypyc-compiled) and the matrix doesn't install
# it -- these tests run in the `types` job. Skip cleanly when mypy is absent.
mypy_api = pytest.importorskip("mypy.api")

_file = Path(__file__)
_dir = _file.parent

def test_dataclass():
    res = mypy_api.run([str(_dir / 'mypy/_dataclass1_ok.py')])
    assert res[2] == 0

    res = mypy_api.run([str(_dir / 'mypy/_dataclass2_error.py')])
    assert res[2] != 0

def test_dispatch():
    res = mypy_api.run([str(_dir / 'mypy/_dispatch1_ok.py')])
    assert res[2] == 0