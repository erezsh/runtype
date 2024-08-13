Dispatch
========

Provides a decorator that enables multiple-dispatch for functions.  Inspired by Julia.

Features:

- Full specificity resolution

- Partial mypy support

- Fast


Decorator
---------

.. autofunction:: runtype.multidispatch

.. autofunction:: runtype.Dispatch

.. autoclass:: runtype.dispatch.MultiDispatch
    :members: choices, feed_token, copy, pretty, resume_parse, exhaust_lexer, accepts, as_immutable

.. autoclass:: runtype.dispatch.DispatchError



What is multiple-dispatch?
--------------------------

Multiple-dispatch is an advanced technique for structuring code, that complements object-oriented programming.

You can think of multiple-dispatch as function overloading on steroids.

In OOP, the type of the object (aka the first argument) always determines the dispatch. Methods of subclasses override the methods of their superclasses. In other words, the more specific type is chosen over the less specific type.

In multiple-dispatch, all the arguments decide together, according the same idea of specificity: The more specific classes (i.e. subclasses) get picked over the less specific types (i.e. superclasses). In cases when the dispatch is ambiguous, which will happen if different parameters can't agree on the correct dispatch, an error will be thrown.

Multiple-dispatch allows you to:

1. Write type-specific functions using a dispatch model that is much more flexible than object-oriented.

2. Group your functions based on "action" instead of based on type.

3. Replace long sequences of "if isinstance" statements


A common way to use multiple-dispatch, is to first implement the most abstract case, and then slowly add special handling for more specific types as required.

It is particularly useful for visiting ASTs.


Runtype's dispatcher
--------------------

Runtype's dispatcher is fast, and will never make an arbitrary choice: in ambiguous situations it will always throw an error.

As a side-effect, it also provides type validation to functions. Trying to dispatch with types that don't match, will result in a dispatch-error.

Dispatch chooses the right function based on the idea specificity, which means that `class MyStr(str)` is more specific than `str`, and so on:

    MyStr(str) < str < Union[int, str] < object

It uses the :doc:`validation <validation>` module as the basis for its type matching, which means that it supports the use of `typing` classes such as `List` or `Union` (See "limitations" for more on that).

Some classes cannot be compared, for example `Optional[int]` and `Optional[str]` are ambiguous for the value `None`. See "ambiguity" for more details.

Users who are familiar with Julia's multiple dispatch, will find runtype's dispatch to be very familiar.

Unlike Julia, Runtype asks to instanciate your own dispatch-group, to avoid collisions between different modules and projects that aren't aware of each other.

Ideally, every project will instanciate Dispatch only once, in a module such as `utils.py` or `common.py`.

Basic Use
---------

Multidispatch groups functions by their name. Functions of different names will never collide with each other.

The order in which you define functions doesn't matter to runtype, but it's recommended to order functions from most specific to least specific.

Example:
::

    from runtype import multidispatch as md

    @dataclass(frozen=False)
    class Point:
        x: int = 0
        y: int = 0
        
        @md
        def __init__(self, points: list | tuple):
            self.x, self.y = points

        @md
        def __init__(self, points: dict):
            self.x = points['x']
            self.y = points['y']
        
    # Test constructors
    p0 = Point()                         # Default constructor
    assert p0 == Point(0, 0)             # Default constructor
    assert p0 == Point([0, 0])           # User constructor
    assert p0 == Point((0, 0))           # User constructor
    assert p0 == Point({"x": 0, "y": 0}) # User constructor


A different dispatch object is created for each module, so collisions between different modules are impossible.

Users who want to define a dispatch across several modules, or to have more granular control, can use the Dispatch class:

::

    from runtype import Dispatch
    dp = Dispatch()

Then, the group can be used as a decorator for any number of functions, in any module.

Functions will still be grouped by name.


Specificity
-----------

When the user calls a dispatched function group, the dispatcher will always choose the most specific function.

If specificity is ambiguous, it will throw a `DispatchError`. Read more in the "ambiguity" section.

Dispatch always chooses the most specific function, across all arguments:

Example:
::

    from typing import Union

    @md
    def f(a: int, b: int):
        return a + b

    @md
    def f(a: Union[int, str], b: int):
        return (a, b)

    ...

    >>> f(1, 2)
    3
    >>> f("a", 2)
    ('a', 2)

Although both functions "match" with `f(1, 2)`, the first definition is unambiguously more specific.


Ambiguity in Dispatch
---------------------

Ambiguity can result from two situations:

1. The argument matches two parameters, and neither is a subclass of the other (Example: `None` matches both `Optional[str]` and `Optional[int]`)

2. Specificity isn't consistent in one function - each argument "wins" in a different function.

Example:
::

    >>> @md
    ... def f(a, b: int): pass
    >>> @md
    ... def f(a: int, b): pass
    >>> f(1, 1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    runtype.dispatch.DispatchError: Ambiguous dispatch

Dispatch is designed to always throw an error when the right choice isn't obvious.

Another example:
::

    >>> @md
    ... def join(seq, sep: str = ''):
    ...    return sep.join(str(s) for s in seq)

    >>> @md
    ... def join(seq, sep: list):
    ...    return join(join(sep, str(s)) for s in seq)

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


Dispatch chooses the right function based on the idea specificity, which means that `class MyStr(str)` is more specific than `str`, and so on: `MyStr(str) < str < Union[int, str] < object`.

MyPy support
------------------------

multidispatch works with mypy by employing the typing.overload decorator, aiding in granular type resolution.

However, due to the limited design of the `typing.overload` decorator, there are several rules that need to be followed, and limitations that should be considered.

1. For MyPy's benefit, more specific functions should be placed above less specific functions.

2. The last dispatched function of each function group, must be written without type declarations (making it the least specific), and use the multidispatch_final decorator. It is recommended to use this function for error handling and default functionality.

Note: Mypy doesn't support all of the functionality of Runtype's dispatch, such as full specificity resolution. Therefore, some valid dispatch constructs will produce an error in mypy.


Example usage:

::

    from runtype import multidispatch as md, multidispatch_final as md_final

    @md
    def join(seq, sep: str = ''):
        return sep.join(str(s) for s in seq)

    @md
    def join(seq, sep: list):
        return join(join(sep, str(s)) for s in seq)

    @md_final
    def join(seq, sep):
        raise NotImplementedError()

    # Calling join() with the wrong types -
    join(1,2)   # At runtime, raises NotImplementedError

    # Mypy generates the following report:
    #   error: No overload variant of "join" matches argument types "int", "int"  [call-overload]
    #   note: Possible overload variants:
    #   note:     def join(seq: Any, sep: str = ...) -> Any
    #   note:     def join(seq: Any, sep: list[Any]) -> Any


Performance
-----------

Multiple-dispatch caches call-signatures by default, and adds a small runtime overhead after the first call.

See :ref:`benchmarks <benchmarks-dispatch>`.

Dispatch is not recommended for use in functions that are called often in time-critical code.

Limitations
-----------

Dispatch currently doesn't support, and will simply ignore:

* keyword arguments (Dispatch relies on the order of the arguments)

* `*args`

* `**kwargs`

These may be implemented in future releases.

Dispatch does not support generics or constraints. Avoid using `List[T]`, `Tuple[T]` or `Dict[T1, T2]` in the function signature. (this is due to conflict with caching, and might be implemented in the future)

`Union` and `Optional` are supported.