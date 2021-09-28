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

Type verification in classes introduces a slight run-time overhead. When running in production, it's recommended to use the `-O` switch for Python. It will skip all `assert`s, and also skip type verification on classes by default.

Alternatively, you can use a shared dataclass decorator, and enable/disable type-checking with a single change.

Example:
  ::
  
    # common.py
    import runtype

    from .settings import DEBUG   # Define DEBUG however you want

    dataclass = runtype.dataclass(check_types=DEBUG)
