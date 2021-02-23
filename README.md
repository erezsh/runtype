# Runtype

Runtype offers fast run-time type validation for Python, by providing utilities for multiple-dispatch and type-safe dataclasses.

Runtype's integration with the `typing` module allows users to invoke type signatures such as `List[int]`, `Dict[str, Optional[str]]`, or `Union[str, Callable]`.

## Multiple Dispatch

Multiple-dispatch is a state-of-the-art technique for structuring code, that complements object-oriented programming.

Unlike in OOP, where the type of the "object" (or: first argument) is always what determines the dispatch, in multiple-dispatch all the arguments decide together, according the idea of specificity: The more specific classes (i.e. subclasses) get picked before the more abstract ones (i.e. superclasses).

That means that when you need to define a logical operation that applies to several types, you can first solve the most abstract case, and then slowly add special handling for more specific types as required. If you ever found yourself writing several "isinstance" in a row, you could probably use multiple-dispatch to write better code!

Runtype's dispatcher is fast, and will never make an arbitrary choice: in ambiguous situations it will always throw an error.

As a side-effect, it also provides type-validation to functions. Trying to dispatch with types that don't match, will result in a dispatch-error.

## Type-Safe Dataclasses

The ability to annotate dataclasses with types has spurred the creation of many great static type-validation tools (such as `mypy`). Unfortunately, they can't always predict what types your dataclasses will receive.

The trouble with storing the wrong data, is that it can just sit there for a while, and by time you get the error, it's hard to track which component or thread put it there.

Runtype provides a `dataclass` drop-in replacement to Python's native dataclass, that validates the types in runtime, and makes sure you'll see the error the moment something goes wrong, and in the right context.

While Runtype's validation can add a small runtime overhead, it's relatively light. And because it's a drop-in replacement, you can always just switch the import back once you're done debugging.

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
def append(a: list, b):
    return a + [b]

@dp
def append(a: tuple, b):
    return a + (b,)

@dp
def append(a: str, b: str):
    return a + b


print( append([1, 2, 3], 4) )        # prints [1, 2, 3, 4]
print( append((1, 2, 3), 4) )        # prints (1, 2, 3, 4)
print( append('foo', 'bar') )        # prints foobar
print( append('foo', 4)     )        # raises DispatchError, no signature for (str, int)


```

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
>>> dict(p)          # Maintains order
{'x': 2, 'y': 3}

>>> p.replace(x=30)  # New instance
Point(x=30, y=3)

>>> Point(10, 3.5)   # Actively validates types
Traceback (most recent call last):
    ...
TypeError: [Point] Attribute 'y' expected value of type <class 'int'>, instead got 3.5
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
Type verification in classes introduces a slight run-time overhead. When running in production, it's recommended to use the `-O` switch for Python. It will skip all `assert`s, and also skip type verification on classes by default (use the `check_types` option to adjust it manually).

Multiple-dispatch caches call-signatures by default (disable at your own risk!), and should add a minimal overhead after the initial resolution. Dispatch is only 5 to 8 times slower than adding two numbers (see: [examples/benchmark\_dispatch](examples/benchmark\_dispatch.py)), which is negligible.

Runtype is not recommended for use in functions that are called often in time-critical code (or classes that are created often).

## License

Runtype uses the [MIT license](LICENSE).

## Donate

If you like Runtype and want to show your appreciation, you can do so at my [patreon page](https://www.patreon.com/erezsh), or [ko-fi page](https://ko-fi.com/erezsh).
