![alt text](logo.png "Logo")


Runtype is a collection of run-time type utilities for Python.

It is:

:runner: Fast! Uses an internal typesystem for maximum performance.

:brain: Smart! Supports `typing`, constraints, auto-casting, and much more.

:gear: Configurative! Write your own type system, and use it with *dataclass* and *dispatch*.

------

### Modules

- :star: [**validation**](https://runtype.readthedocs.io/en/latest/validation.html) - Provides a smarter alternative to `isinstance` and `issubclass`, with support for the `typing` module, and type constraints.

- :star: [**dataclass**](https://runtype.readthedocs.io/en/latest/dataclass.html) - Adds run-time type validation to the built-in dataclass.

    - Improves dataclass ergonomics.
    - Supports automatic value casting, Pydantic-style. (Optional, off by default)
    - Supports types with constraints. (e.g. `String(max_length=10)`)
    - Supports optional sampling for faster validation of big lists and dicts.
    - 40% faster than Pydantic ([read here](https://runtype.readthedocs.io/en/latest/dataclass.html#compared-to-pydantic))

- :star: [**dispatch**](https://runtype.readthedocs.io/en/latest/dispatch.html) - Provides fast multiple-dispatch for functions and methods, via a decorator.

    - Inspired by Julia.

- :star: [**type utilities**](https://runtype.readthedocs.io/en/latest/types.html) - Provides a set of classes to implement your own type-system.

    - Used by runtype itself, to emulate the Python type-system.


## Docs

Read the docs here: https://runtype.readthedocs.io/

## Install

```bash
pip install runtype
```

No dependencies.

Requires Python 3.6 or up.

[![Build Status](https://travis-ci.org/erezsh/runtype.svg?branch=master)](https://travis-ci.org/erezsh/runtype)
[![codecov](https://codecov.io/gh/erezsh/runtype/branch/master/graph/badge.svg)](https://codecov.io/gh/erezsh/runtype)

## Examples

### Validation (Isa & Subclass)

```python
from typing import Dict, Mapping
from runtype import isa, issubclass

print( isa({'a': 1}, Dict[str, int]) )
#> True
print( isa({'a': 'b'}, Dict[str, int]) )
#> False

print( issubclass(Dict[str, int], Mapping[str, int]) )
#> True
print( issubclass(Dict[str, int], Mapping[int, str]) )
#> False
```

### Dataclasses

```python
from typing import List
from datetime import datetime
from runtype import dataclass

@dataclass(check_types='cast')  # Cast values to the target type, when applicable
class Person:
    name: str
    birthday: datetime = None   # Optional
    interests: List[str] = []   # The list is copied for each instance


print( Person("Beetlejuice") )
#> Person(name='Beetlejuice', birthday=None, interests=[])
print( Person("Albert", "1955-04-18T00:00", ['physics']) )
#> Person(name='Albert', birthday=datetime.datetime(1955, 4, 18, 0, 0), interests=['physics'])
print( Person("Bad", interests=['a', 1]) )
# Traceback (most recent call last):
#   ...
# TypeError: [Person] Attribute 'interests' expected value of type list[str]. Instead got ['a', 1]

#     Failed on item: 1, expected type str

```

### Multiple Dispatch

```python
from runtype import Dispatch
dp = Dispatch()

@dp
def append(a: list, b):
    return a + [b]

@dp
def append(a: tuple, b):
    return a + (b,)

@dp
def append(a: str, b: str):
    return a + b


print( append([1, 2, 3], 4) )
#> [1, 2, 3, 4]
print( append((1, 2, 3), 4) )
#> (1, 2, 3, 4)
print( append('foo', 'bar') )
#> foobar
print( append('foo', 4)     )
# Traceback (most recent call last):
#    ...
# runtype.dispatch.DispatchError: Function 'append' not found for signature (<class 'str'>, <class 'int'>)
```


## License

Runtype uses the [MIT license](LICENSE).

## Donate

If you like Runtype and want to show your appreciation, you can do so at my [patreon page](https://www.patreon.com/erezsh), or [ko-fi page](https://ko-fi.com/erezsh).
