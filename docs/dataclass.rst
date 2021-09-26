Dataclass
=========

Decorator
---------

.. autofunction:: runtype.dataclass.dataclass

Part of the added ergonomics and functionality were influenced by Pydantic:

- Members that are assigned ``None``, automatically become ``Optional``. (Unless specified otherwise through ``config``)

- Members without a default value, following members with a default value, are now allowed (and will fail if not assigned on init).



Added methods
-------------

The following functions, which are available as at the module level, will also be available as methods of the dataclass instances.
These methods won't override existing ones; They will be added only if the names aren't already used.

.. autofunction:: runtype.dataclass.replace

.. autofunction:: runtype.dataclass.astuple

.. autofunction:: runtype.dataclass.aslist

.. autofunction:: runtype.dataclass.json


Configuration
-------------

.. autoclass:: runtype.dataclass.Configuration

.. autoclass:: runtype.dataclass.PythonConfiguration



Performance
-----------

(debug vs production; optimize mode)

Runtype's type-checking is fast and optimized, and yet, type-checking every instance may slow down your program considerably.

If you're running in production, consider using Python's optimize flag (`python -O ...`), which will disable dataclass type-checking. (it also disables asserts)

Alternatively, you can use a shared dataclass decorator, and enable/disable type-checking with a single change.

Example:
  ::
  
    # common.py
    import runtype

    from .settings import DEBUG   # Define DEBUG however you want

    dataclass = runtype.dataclass(check_types=DEBUG)
