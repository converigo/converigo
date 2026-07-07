from __future__ import annotations

import importlib
from pathlib import Path
from typing import Iterable, List, Type

from app.plugins.base import ConverterPlugin

PACKAGE_NAME = "app.plugins"


def _iter_plugin_module_names() -> Iterable[str]:
    plugins_root = Path(__file__).parent
    for path in plugins_root.rglob("*.py"):
        if path.name == "__init__.py":
            continue

        module_path = path.relative_to(plugins_root).with_suffix("")
        yield ".".join([PACKAGE_NAME, *module_path.parts])


def discover_plugin_classes() -> List[Type[ConverterPlugin]]:
    discovered: List[Type[ConverterPlugin]] = []
    for module_name in _iter_plugin_module_names():
        module = importlib.import_module(module_name)
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if (
                isinstance(attribute, type)
                and issubclass(attribute, ConverterPlugin)
                and attribute is not ConverterPlugin
            ):
                discovered.append(attribute)
    return discovered
