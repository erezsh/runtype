# Runtype

**runtype** is composed of several utility modules:

1. [**dispatch**](dispatch.md) - Provides a decorator for fast multi-dispatch at run-time for functions, with sophisticated ambiguity resolution.

2. [**dataclass**](dataclass.md) - Improves on Python's existing dataclass, by verifying the type-correctness of its attributes at run-time. Also provides a few useful methods for dataclasses.

3. [**isa**](isa.md) - Provides alternative functions to `isinstance` and `issubclass`, that understand Python's `typing` module.

Runtype's integration with the `typing` module allows to use type signatures such as `List[int]`, `Optional[str]`, or `Union[int, str, Callable]`.

Click on each one to learn more.

## Install

```bash
$ pip install runtype
```

No dependencies.

Requires Python 3.7 or up (or Python 3.6 with the dataclasses backport)

[![Build Status](https://travis-ci.org/erezsh/runtype.svg?branch=master)](https://travis-ci.org/erezsh/runtype)
[![codecov](https://codecov.io/gh/erezsh/runtype/branch/master/graph/badge.svg)](https://codecov.io/gh/erezsh/runtype)

## Performance
Type verification in classes introduces a slight run-time overhead.

Multiple-dispatch caches call-signatures by default (disable at your own risk!), and should add a minimal overhead after the initial resolution. Dispatch is only 5 to 8 times slower than adding two numbers (see: [examples/benchmark\_dispatch](examples/benchmark\_dispatch.py)), which is negligable.

Runtype is not recommended for use in functions that are called often in time-critical code (or classes that are created often).

## License

Runtype uses the [MIT license](LICENSE).

## Similar projects

* [typical](https://github.com/seandstewart/typical) - Provides type verification for classes and methods, with a focus on type coercion.