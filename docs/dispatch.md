# dispatch.py

The `dispatch` module provides a decorator that enables multiple-dispatch for functions.

Multiple-dispatch allows you to:

1. Write type-specific functions using a dispatch model that is much more flexible than object-oriented.

2. Group your functions based on "action" instead of based on type.

Dispatch uses the [`isa`](isa.md) module as the basis for its type matching, which means that it supports the use of `typing` classes (See "limitations" for more on that).

Users who are familiar with Julia's multiple dispatch, will find runtype's dispatch to be very familiar.

## Basic Use

First, users must instanciate the `Dispatch` object, to create a dispatch group:
```python
from runtype import Dispatch
dp = Dispatch()
```

Then, the group can be used as a decorator for any number of functions.

Dispatch maintains the original name of every function. So, functions of different names will never collide with each other.

Example:
```python
@dp
def f(a: int):
    print("Got int:", a)

@dp
def f(a):   # No type means Any type
    print("Got:", a)

@dp
def g(a: str):
    print("Got string in g:", a)

...

>>> f(1)
Got int: 1
>>> f("a")
Got: a
>>> g("a")
Got string in g: a
```

The order in which you define functions doesn't matter.

## Specificity

When the user calls a dispatched function group, the dispatcher will always choose the most specific function.

If specificity is ambiguous, it will throw a `DispatchError`. Read more in the "ambiguity" section.

Dispatch always chooses the most specific function, across all arguments:

Example:

```python
from typing import Union

@dp
def f(a: int, b: int):
    return a + b

@dp
def f(a: Union[int, str], b: int):
    return (a, b)

...

>>> f(1, 2)
3
>>> f("a", 2)
('a', 2)
```

Although both functions "match" with `f(1, 2)`, the first definition is unambiguously more specific.


## Ambiguity in Dispatch

Ambiguity can result from two situations:

1. The argument matches two parameters, and neither is a subclass of the other (Example: `None` matches both `Optional[str]` and `Optional[int]`)

2. Specificity isn't consistent in one function - each argument "wins" in a different function.

Example:
```python
>>> @dp
... def f(a, b: int): pass
>>> @dp
... def f(a: int, b): pass
>>> f(1, 1)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
runtype.dispatch.DispatchError: Ambiguous dispatch
```

Dispatch is designed to always throw an error when the right choice isn't obvious.

## Performance

Multiple-dispatch caches call-signatures by default (disable at your own risk!), and should add a minimal runtime overhead after the initial resolution. A single dispatch of two arguments is only 5 to 8 times slower than adding two numbers (see: [examples/benchmark\_dispatch](https://github.com/erezsh/runtype/blob/master/examples/benchmark_dispatch.py)), which is negligable for most use-cases.

## Limitations

Dispatch currently doesn't support:

* keyword arguments

* `*args`

* `**kwargs`

These may be implemented in future releases.

Dispatch uses the `isa` module as the basis for its type matching, and so it inherits `isa`'s limitations as well.

Dispatch does not support generics. Avoid using `List[T]`, `Tuple[T]` or `Dict[T1, T2]` in the function signature. (this is due to conflict with caching, and might be implemented in the future)

`Union` and `Optional` are supported.