# CHANGES

## 0.2.3

- Bugfix for use of `dataclasses.field`

## 0.2.2

- Various fixes
- Added `check_types='sample'`

## 0.2.1

- Fix for 0.2.0

## 0.2.0

- Rewrote `isa` to use our own PythonType hierarchy instead of Python's typing classes, for a huge performance boost

- Added support for Literal, Mapping, collections.abc, set, frozenset

- Added support for assigning default mutables (e.g. `a: list = []`)

- Added auto-casting support, with `dataclass(check_types='cast')`
	- str -> datetime
	- str -> int
	- int -> float

- Added support for value constraints
	- Int(min, max)
	- String(min_length)

- Added support for auto Optional by defaulting to None

- Refactored ensure_isa -> Configuration

- Added support for required keyword (i.e. without a default value, after defaults are already specified)

- Various bugfixes

## 0.1.7