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


Casting
-------

When called with the option ``check_types="cast"``, values that are provided to instanciate the dataclass will be cast instead of validated.

Runtype will only attempt to cast in situations when no data is lost when converting the value.

The following casts are currently implemented:

- str -> int

- str -> datetime

- int -> float

If a cast fails, Runtype raises a `TypeError`. (same as when validation fails)

More casts will be added in time.

For non-builtin types, Runtype will attempt to call the `cast_from` class-method, if one exists.

Example:
::

    @dataclass
    class Name:
        first: str
        last: str = None

        @classmethod
        def cast_from(cls, s: str):
            return cls(*s.split())

    @dataclass(check_types='cast')
    class Person:
        name: Name

    p = Person("Albert Einstein")
    assert p.name.first == 'Albert'
    assert p.name.last == 'Einstein'
  

Sampling
---------

When called with the option ``check_types="sample"``, lists and dictionaries will only have a sample of their items validated, instead of each item.

This approach will validate big lists and dicts much faster, but at the cost of possibly missing anomalies in them.


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

Using Pydantic's own benchmark, runtype performs twice faster than Pydantic. (or, Pydantic is twice slower than Runtype)

::
          pydantic best=63.839μs/iter avg=65.501μs/iter stdev=1.763μs/iter version=1.9.1
    attrs + cattrs best=45.607μs/iter avg=45.804μs/iter stdev=0.386μs/iter version=21.4.0
           runtype best=31.500μs/iter avg=32.281μs/iter stdev=0.753μs/iter version=0.2.7

See the code `here <https://github.com/samuelcolvin/pydantic/pull/3264>`_.
