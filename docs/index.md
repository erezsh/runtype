# Runtype

**runtype** is composed of several utility modules:

1. [**dispatch**](dispatch.md) - Provides a decorator for fast multi-dispatch at run-time for functions, with sophisticated ambiguity resolution.

2. [**dataclass**](dataclass.md) - Improves on Python's existing dataclass, by verifying the type-correctness of its attributes at run-time. Also provides a few useful methods for dataclasses.

3. [**isa**](isa.md) - Provides alternative functions to `isinstance` and `issubclass`, that undestand Python's `typing` module.

Runtype's integration with the `typing` module allows to use type signatures such as `List[int]`, `Optional[str]`, or `Union[int, str, Callable]`.

## Install

```bash
$ pip install runtype
```

No dependencies.

Requires Python 3.7 or up (or Python 3.6 with the dataclasses backport)
