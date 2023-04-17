"""Plugin for mypy

To use, add this to mypy.ini:

[mypy]
plugins = runtype.mypy

"""

from typing import Callable, Optional, Type

from mypy.plugin import ClassDefContext, Plugin
from mypy.plugins import dataclasses

DATACLASS_PATHS = {"runtype.dataclass.dataclass"}


def plugin(version: str) -> "Type[Plugin]":
    """
    `version` is the mypy version string
    We might want to use this to print a warning if the mypy version being used is
    newer, or especially older, than we expect (or need).
    """
    return RuntypePlugin


class RuntypePlugin(Plugin):
    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname in DATACLASS_PATHS:
            return dataclasses.dataclass_class_maker_callback
        return None
