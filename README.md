# Runtype

**runtype** is composed of several utility modules:

1. **dispatch** - Provides a decorator for fast multi-dispatch at run-time for functions, with sophisticated ambiguity resolution.

2. **dataclass** - Improves on Python's existing dataclass, by verifying the type-correctness of its attributes at run-time. Also provides a few useful methods for dataclasses.

3. **isa** - Provides alternative functions to `isinstance` and `issubclass`, that undestand Python's `typing` module.

Runtype's integration with the `typing` module allows to use type signatures such as `List[int]`, `Optional[str]`, or `Union[int, str, Callable]`.

## Docs

Read the docs here: https://runtype.readthedocs.io/

## Install

```bash
$ pip install runtype
```

No dependencies.

Requires Python 3.7 or up (or Python 3.6 with the dataclasses backport)

[![Build Status](https://travis-ci.org/erezsh/runtype.svg?branch=master)](https://travis-ci.org/erezsh/runtype)
[![codecov](https://codecov.io/gh/erezsh/runtype/branch/master/graph/badge.svg)](https://codecov.io/gh/erezsh/runtype)

## Examples

### Multiple Dispatch

```python
from runtype import Dispatch
dp = Dispatch()

@dp
def join(seq, sep: str = ''):
    return sep.join(str(s) for s in seq)

@dp
def join(seq, sep: list):
    return join(join(sep, str(s)) for s in seq)
...

>>> join([0, 0, 7])                 # -> 1st definition
'007'

>>> join([1, 2, 3], ', ')           # -> 1st definition
'1, 2, 3'

>>> join([0, 0, 7], ['(', ')'])     # -> 2nd definition
'(0)(0)(7)'

>>> join([1, 2, 3], 0)              # -> no definition
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  ...
runtype.dispatch.DispatchError: Function 'join' not found for signature (<class 'list'>, <class 'int'>)

```

Dispatch chooses the right function based on the idea specificity, which means that `class MyStr(str)` is more specific than `str`, and so on: `MyStr(str) < str < Union[int, str] < object`.

### Dataclasses

Basic usage:

```python
>>> from runtype import dataclass

>>> @dataclass
>>> class Point:
...     x: int
...     y: int

>>> p = Point(2, 3)
>>> p
Point(x=2, y=3)
>>> dict(p)         # Maintains order
{'x': 2, 'y': 3}

>>> p.replace(x=30)  # New instance
Point(x=30, y=3)
```

Using advanced types:

```python
>>> from typing import Optional, Callable
>>> from runtype import dataclass

>>> @dataclass
>>> class Animal:
...     name: str
...     make_sound: Optional[Callable] = None

>>> Animal("Ant")
Animal(name='Ant', make_sound=None)

>>> Animal("Cat", lambda: print("meow"))
Animal(name='Cat', make_sound=<function <lambda> at ...>)

>>> Animal("Dog", "woof")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  ...
[Animal] Attribute 'make_sound' expected value of type typing.Union[typing.Callable, NoneType], instead got 'woof'
```

## Performance
Type verification in classes introduces a slight run-time overhead.

Multiple-dispatch caches call-signatures by default (disable at your own risk!), and should add a minimal overhead after the initial resolution. Dispatch is only 5 to 8 times slower than adding two numbers (see: [examples/benchmark\_dispatch](examples/benchmark\_dispatch.py)), which is negligable.

Runtype is not recommended for use in functions that are called often in time-critical code (or classes that are created often).

### Similar projects

* [typical](https://github.com/seandstewart/typical) - Provides type verification for classes and methods, with a focus on type coercion.


## License

Runtype uses the [MIT license](LICENSE).

## Donate

If you like Runtype and want to show your appreciation, you can do so at my [patreon page](https://www.patreon.com/erezsh), or [ko-fi page](https://ko-fi.com/erezsh).
