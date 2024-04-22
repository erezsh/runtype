from pathlib import Path

import mypy
import mypy.api

_file = Path(__file__)
_dir = _file.parent

def test_dataclass():
    res = mypy.api.run([str(_dir / 'mypy/_dataclass1_ok.py')])
    assert res[2] == 0

    res = mypy.api.run([str(_dir / 'mypy/_dataclass2_error.py')])
    assert res[2] != 0

def test_dispatch():
    res = mypy.api.run([str(_dir / 'mypy/_dispatch1_ok.py')])
    assert res[2] == 0