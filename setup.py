import re
from setuptools import setup

__version__ ,= re.findall('__version__ = "(.*)"', open('runtype/__init__.py').read())

setup(
    name = "runtype",
    version = __version__,
    packages = ['runtype'],

    requires = [],
    install_requires = [],

    package_data = { '': ['*.md'] },

    test_suite = 'tests.__main__',

    # metadata for upload to PyPI
    author = "Erez Shinan",
    author_email = "erezshin@gmail.com",
    description = "Type dispatch and validation for run-time",
    license = "MIT",
    keywords = "types typing dispatch dataclass runtime",
    url = "https://github.com/erezsh/runtype",
    download_url = "https://github.com/erezsh/runtype/tarball/master",
    long_description='''
Runtype is a collection of run-time type utilities for Python.

It is:

🏃 Fast! (benchmarks coming soon)

🧠 Smart! Supports typing, constraints, auto-casting, and much more.

⚙️ Very customizable. You can use dataclass and dispatch with your own typesystem!

Modules
⭐ validation - Provides a smarter alternative to isinstance and issubclass

    Supports typing module, and type constraints.

⭐ dataclass - Adds run-time type validation to the built-in dataclass.

    Improves dataclass ergonomics.
    Supports automatic value casting, Pydantic-style. (Optional, off by default)
    Supports types with constraints. (e.g. String(max_length=10))

⭐ dispatch - Provides fast multiple-dispatch for functions and methods, via a decorator.

    Inspired by Julia.

⭐ base_types - Provides a set of classes to implement your own type-system.

    Used by runtype itself, to emulate the Python type-system.

''',

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)

