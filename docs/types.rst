Type Utilities
==============

Runtype includes building blocks for making your own type-system.

You can use that type-system to:

- reason about your program's logic

- supply it for runtype to use in dispatch and validation.


Types
-----

Note: These types are not specific to the Python type-system!

.. autoclass:: runtype.base_types.Type

.. autoclass:: runtype.base_types.AnyType

.. autoclass:: runtype.base_types.DataType

.. autoclass:: runtype.base_types.SumType

.. autoclass:: runtype.base_types.ProductType

.. autoclass:: runtype.base_types.ContainerType

.. autoclass:: runtype.base_types.GenericType

.. autoclass:: runtype.base_types.PhantomType

.. autoclass:: runtype.base_types.PhantomGenericType