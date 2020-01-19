# dispatch.py

The `dispatch` module provides a decorator that enables multiple-dispatch for functions.

### What is multiple-dispatch?

Multiple-dispatch is a state-of-the-art technique for structuring code, that complements object-oriented programming.

Unlike in OOP, where the type of the "object" (or: first argument) is always what determines the dispatch, in multiple-dispatch all the arguments decide together, according the idea of specificity: The more specific classes (i.e. subclasses) get picked before the more abstract ones (i.e. superclasses).

That means that when you need to define a logical operation that applies to several types, you can first solve the most abstract case, and then slowly add special handling for more specific types as required. If you ever found yourself writing several "isinstance" in a row, you could probably use multiple-dispatch to write better code!

Multiple-dispatch allows you to:

1. Write type-specific functions using a dispatch model that is much more flexible than object-oriented.

2. Group your functions based on "action" instead of based on type.

You can think of multiple-dispatch as function overloading on steroids.

### Runtype's dispatcher

Runtype's dispatcher is fast, and will never make an arbitrary choice: in ambiguous situations it will always throw an error.

As a side-effect, it also provides type-validation to functions. Trying to dispatch with types that don't match, will result in a dispatch-error.

Dispatch chooses the right function based on the idea specificity, which means that `class MyStr(str)` is more specific than `str`, and so on:

    MyStr(str) < str < Union[int, str] < object

It uses the [`isa`](isa.md) module as the basis for its type matching, which means that it supports the use of `typing` classes such as `List` or `Union` (See "limitations" for more on that).

Some classes cannot be compared, for example `Optional[int]` and `Optional[str]` are ambiguous for the value `None`. See "ambiguity" for more details.

Users who are familiar with Julia's multiple dispatch, will find runtype's dispatch to be very familiar.

Unlike Julia, Runtype asks to instanciate your own dispatch-group, to avoid collisions between different modules and projects that aren't aware of each other.

Ideally, every project will instanciate Dispatch only once, in a module such as `utils.py` or `common.py`.

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

Dispatch currently doesn't support, and will simply ignore:

* keyword arguments (Dispatch relies on the order of the arguments)

* `*args`

* `**kwargs`

These may be implemented in future releases.

Dispatch uses the `isa` module as the basis for its type matching, and so it inherits `isa`'s limitations as well.

Dispatch does not support generics. Avoid using `List[T]`, `Tuple[T]` or `Dict[T1, T2]` in the function signature. (this is due to conflict with caching, and might be implemented in the future)

`Union` and `Optional` are supported.