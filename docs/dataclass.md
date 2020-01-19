# dataclass.py

The `dataclass` module replaces and expands on Python's built-in dataclasses.

Dataclasses are especially useful for passing around different components, when thought of as named-tuples with methods (and typed too!).

These are the differences:

1. Type validation - all the annotated attributes are validated, with `typing` support, when the dataclass is created.

2. Frozen by default - which allows for automatic comparison and hashing based on the annotated attributes.

3. Convenience methods - operations such as `x.replace(attr=value)` and others, instead of the built-in functions.

## Type validation

Runtype's dataclass tests every annotated attribute against its annotation, when instanciating a dataclass, or when changing one of its attributes (when `frozen=False`).

Runtype supports annotations with `typing` classes, by using the [`isa` module](isa.md).

Example:

```python
from typing import Optional
from runtype import dataclass

@dataclass
class A:
    a: int
    b: Optional[int]

...

>>> A(1, None).replace(b=2)
A(a=1, b=2)

>>> dict(A(1, 2))
{'a': 1, 'b': 2}

>>> A(None, 1)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: [A] Attribute 'a' expected value of type <class 'int'>, instead got None
```


## Custom validation

It's possible to provide your own `isinstance` replacement when creating a dataclass, instead of `isa`.

Example:

```python
@dataclass(isinstance=lambda a, b: a in b)
class Form:
    answer1: ("yes", "no")
    score: range(1, 11)

...

>>> Form("no", 3)
Form(answer1='no', score=3)

>>> Form("no", 12)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: [Form] Attribute 'score' expected value of type range(1, 11), instead got 12
```
## Methods

* `.replace(**delta)` - Returns a new instance, with the given attibutes and values overwriting the existing ones.

* `.astuple()` - Returns a tuple of the values

* `.aslist()` - Returns a list of the values

* `dict(dataclass_instance)` - Returns a dict of the annotated attributes and values
