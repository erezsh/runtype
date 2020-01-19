# isa.py

The `isa` module provides two main functions:

* `isa` - a replacement for `isinstance`

* `issubclass` - a replacement for the built-in `issubclass`

Both functions improve on the built-ins by also accepting `typing` classes.

## Features

Supported classes include: `List`, `Tuple`, `Dict`, `Union`, `Optional`, `Callable`, and of course `Any`.

`isa(x, Any)` and `issubclass(x, Any)` always return `True`.

### Element-wise validation

Testing `isa` with `List[T]`, `Tuple[T1, T2, T3]` and `Dict[T1, T2]` will iterate over each element and call `isa(elem, T)` recursively.

Example:
```python
>>> isa([1,2], List[int])
True
>>> isa([1,"a"], List[int])
False
>>> isa([1,"a"], Tuple[int, str])
True
```

### Limitations

Full type logic isn't yet supported:
```python
>>> issubclass(int, Union[int, str])    # OK
True
>>> issubclass(List[int], List[Union[int, str]])    # Should also return True
False
```

This might be fixed in future versions. Open an issue to motivate me to solve it.