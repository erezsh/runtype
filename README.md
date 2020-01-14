# Runtype

(Work In Progress! Check back in a few days)

**runtype** is composed of several utility modules:

1. **dispatch** - Provides a decorator for fast multi-dispatch at run-time for functions, with sophisticated ambiguity resolution.

2. **dataclass** - Improves on Python's existing dataclass, by verifying the type-correctness of its attributes at run-time. Also provides a few useful methods for dataclasses.

3. **isa** - Provides alternative functions to `isinstance` and `issubclass`, that undestand Python's `typing` module.

Runtype's integration with the `typing` module allows to use type signatures such as `List[int]`, `Optional[str]`, or `Union[int, str, Callable]`.

## Install

```bash
$ pip install runtype
```

No dependencies.

## Example

### Multiple Dispatch

```python
>>> from runtype import Dispatch
>>> dp = Dispatch()
>>> @dp
... def add1(i: Optional[int]):
...     return i + 1
>>> @dp
... def add1(s: Optional[str]):
...     return s + "1"
>>> @dp
... def add1(a):  # Any, which is the least-specific
...     return (a, 1)
>>> add1(1)
2
>>> add1("1")
11
>>> add1(1.0)
(1.0, 1)
>>> add1(None)  # Uh oh! The first two functions are both specific enough!
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  ...
runtype.dispatch.DispatchError: Ambiguous dispatch: Unable to resolve specificity of types: (<class 'str'>, <class 'NoneType'>), (<class 'int'>, <class 'NoneType'>)

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

### Performance
Type verification introduces a slight run-time overhead, but dataclasses already present such an overhead,
and should be in general avoided in time-critical parts of the code, for classes of mass instances.

Multiple-dispatch caches call-signatures by default (disable at your own risk!), and should add a minimal overhead after the initial resolution. Still, it's not recommended for use in functions that are called often in time-critical code.

### Similar projects

* [typical](https://github.com/seandstewart/typical) - Provides type verification for classes and methods, with a focus on type coercion.

