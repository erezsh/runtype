Typing support
==============

Runtype supports a wide-range of types and typing constructs, however full-support is still work in progress.

For now, some constructs are available for validation, but not for dispatch.

Here is the detailed list:

.. list-table::
   :widths: 25 25 25
   :header-rows: 1

   * - Types / Constructs
     - Validation
     - Dispatch
   * - Primitives (None, bool, float, int, str, etc.)
     - ✔
     - ✔
   * - Date primitives (datetime, date, time, timedelta)
     - ✔
     - ✔
   * - Containers, non-generic  (list, tuple, dict)
     - ✔
     - ✔
   * - Callable, non-generic (callable)
     - ✔
     - ✔
   * - abc.Set, abc.MutableMapping, etc.
     - ✔
     - ✔
   * - typing.AbstractSet
     - ✔
     - ✔
   * - typing.Any
     - ✔
     - ✔
   * - typing.Union, Optional
     - ✔
     - ✔
   * - typing.Type (Type[x])
     - ✔
     - ✔
   * - typing.Literal
     - ✔
     - ✔
   * - Generic containers (list[x], tuple[x], dict[x])
     - ✔
     - TODO
   * - Infinite tuple (tuple[x, ...])
     - ✔
     - TODO
   * - Generic callable
     - TODO
     - TODO
   * - typing.IO
     - TODO
     - TODO
   * - TypeVar
     - TODO
     - TODO
   * - Protocol
     - TODO
     - TODO
