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