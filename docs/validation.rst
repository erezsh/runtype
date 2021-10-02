Validation (isa & issubclass)
=============================

This module provides type validation functions for Python with support for the ``typing`` module.

You may use them to replace ``isinstance()`` and ``issubclass``.

It uses the same validation mechanism as used by 'dataclass' and 'dispatch' in order to resolve and validate types and values.

Functions
---------

.. autofunction:: runtype.validation.isa

.. autofunction:: runtype.validation.ensure_isa

.. autofunction:: runtype.validation.assert_isa

.. autofunction:: runtype.validation.issubclass

.. autofunction:: runtype.validation.is_subtype


Element-wise validation
-----------------------

When called on generics such as `List`, `Tuple`, `Set` and `Dict`, runtype will iterate over each element and call `ensure_isa()` recursively.

Example:
::

	>>> isa([1,2], List[int])
	True

	>>> isa([1,"a"], List[int])
	False

	>>> isa([{1: 2}], List[Dict[int, int]])
	True
	
	>>> isa([{1: 2}], List[Dict[int, str]])
	False


How does it work?
-----------------

Runtype maps the given types onto an internal type system, that is capable of expressing the Python type system.

In order to validate a value against a type, we do the following:

1. Convert (cast) the given type into an instance of `PythonType`, that represents the given type within the internal type system. This operation is cached.

2. Call the `PythonType.validate_instance()` method with the given value. Each subclass has its own implementation. For example:

	- In `PythonDataType` (e.g. `Int` or `DateTime`), the method will simply call Python's `isinstance()` on the value.

	- In `SequenceType` (e.g. `List` or `Iter`), after `isinstance()`, this method will call itself recursively for each item.

The internal type system is implemented using the :doc:`types` module.
