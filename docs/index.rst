.. Runtype documentation master file, created by
   sphinx-quickstart on Sun Aug 16 13:09:41 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Runtype's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Modules
   :hidden:

   validation
   dataclass
   dispatch
   types


Runtype is a collection of run-time type utilities for Python.

It contains the following user-facing modules:

   -  :doc:`validation` - Alternatives to 'isinstance' and 'issubclass'
   -  :doc:`dataclass` - Type-validation in dataclasses
   -  :doc:`dispatch` - Multiple dispatch
   -  :doc:`types` - Utilities for creating type systems


Install
-------
::

   pip install runtype

No dependencies.

Requires Python 3.6 or up.


ArchLinux
~~~~~~~~~

ArchLinux users can install the package by running:
::

  yay -S python-runtype