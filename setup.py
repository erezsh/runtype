import re
from setuptools import setup

# __version__ ,= re.findall('__version__ = "(.*)"', open('lark/__init__.py').read())
__version__ = '0.1a'

setup(
    name = "runtype",
    version = __version__,
    packages = [''],

    requires = [],
    install_requires = [],

    package_data = { '': ['*.md', '*.lark'] },

    # test_suite = 'tests.__main__',

    # metadata for upload to PyPI
    author = "Erez Shinan",
    author_email = "erezshin@gmail.com",
    description = "Type dispatch and validation for run-time",
    license = "MIT",
    keywords = "types",
    url = "https://github.com/erezsh/runtype",
    # download_url = "https://github.com/erezsh/lark/tarball/master",
    long_description='''
    To come
''',

    classifiers=[
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        # "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        # "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
    ],

)

