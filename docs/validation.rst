Validation (isa & issubclass)
=============================

This module provides type validation function for Python with support for the ``typing`` module.

You may use them to replace ``isinstance()`` and ``issubclass``.

These methods are also used by 'dataclass' and 'dispatch' in order to resolve and validate types and values.


Functions
---------

.. autofunction:: runtype.isa.isa

.. autofunction:: runtype.isa.issubclass

.. autofunction:: runtype.isa.is_subtype

.. autofunction:: runtype.isa.ensure_isa

.. autofunction:: runtype.isa.assert_isa

Element-wise validation
-----------------------

Testing `isa` with `List[T]`, `Tuple[T1, T2, T3]` and `Dict[T1, T2]` will iterate over each element and call `isa(elem, T)` recursively.

Example:
::

	>>> isa([1,2], List[int])
	True
	>>> isa([1,"a"], List[int])
	False
