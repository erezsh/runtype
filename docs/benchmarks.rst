Benchmarks
==========

The following benchmarks were run using `pytest-benchmark` and plotted using `matplotlib`.

The code for running and plotting these benchmarks is included in the repo.
See: ``docs/generate_benchmarks.sh``

Benchmark contributions for more use-cases or new libraries are welcome!


Validation (isinstance)
-----------------------

In the image below, we compare runtype to its (only?) competitor, the library `beartype <https://github.com/beartype/beartype>`_.

We can see the native ``isinstance()`` is faster than runtype's ``isa()``. However, it isn't quite a fair comparison,
because it doesn't support all the types that ``isa()`` supports.

.. image:: bench_validation.jpg


Dispatch
--------

In the images below, we compare runtype's multiple dispatch to its (only?) competitor, the library `plum <https://github.com/beartype/plum>`_.

We can see that the naive approach of using if-else is faster for a small amount of branches,
but by 32 branches runtype is already significantly faster.

Curiously, for dispatching to unions of types, runtype is twice faster (!) than the naive if-else approach,
even for a very low number of branches.

.. image:: bench_dispatch.jpg

.. image:: bench_dispatch_union.jpg