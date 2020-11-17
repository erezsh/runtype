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
runtype is composed of several utility modules:

1. dispatch - Provides a decorator for fast multi-dispatch at run-time for functions, with sophisticated ambiguity resolution.

2. dataclass - Improves on Python's existing dataclass, by verifying the type-correctness of its attributes at run-time. Also provides a few useful methods for dataclasses.

3. isa - Provides alternative functions to `isinstance` and `issubclass`, that undestand Python's `typing` module.

Runtype's integration with the `typing` module allows to use type signatures such as `List[int]`, `Optional[str]`, or `Union[int, str, Callable]`.
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

