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
  :members: ensure_isa, cast, canonize_type, on_default


.. autoclass:: runtype.dataclass.PythonConfiguration



Performance
-----------

Type verification in classes introduces a small run-time overhead.

When running in production, it's recommended to use the `-O` switch for Python. It will make Runtype skip type verification in dataclasses. (unless `check_types` is specified.)

Alternatively, you can use a shared dataclass decorator, and enable/disable type-checking with a single change.

Example:
  ::
  
    # common.py
    import runtype

    from .settings import DEBUG   # Define DEBUG however you want

    dataclass = runtype.dataclass(check_types=DEBUG)


Compared to Pydantic
~~~~~~~~~~~~~~~~~~~~

Using Pydantic's own benchmark, runtype performs 40% faster than Pydantic. (or, Pydantic 30% slower than Runtype)

::

          pydantic best=70.296μs/iter avg=79.918μs/iter stdev=11.326μs/iter version=1.8.1
    attrs + cattrs best=75.502μs/iter avg=85.398μs/iter stdev=6.485μs/iter version=21.2.0
           runtype best=49.468μs/iter avg=57.926μs/iter stdev=11.853μs/iter version=0.2.1


See the code `here <https://github.com/samuelcolvin/pydantic/pull/3264>`_.
