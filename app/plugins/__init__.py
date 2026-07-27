from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Iterable, List, Type

from app.plugins.base import ConverterPlugin

PACKAGE_NAME = "app.plugins"


@dataclass(frozen=True)
class PluginDiscoverySkip:
    module_name: str
    reason: str


@dataclass(frozen=True)
class PluginDiscoveryResult:
    plugin_classes: List[Type[ConverterPlugin]]
    skipped_plugins: List[PluginDiscoverySkip]


def _iter_plugin_module_names() -> Iterable[str]:
    plugins_root = Path(__file__).parent
    for path in plugins_root.rglob("*.py"):
        if path.name == "__init__.py":
            continue

        module_path = path.relative_to(plugins_root).with_suffix("")
        yield ".".join([PACKAGE_NAME, *module_path.parts])


def discover_plugins() -> PluginDiscoveryResult:
    discovered: List[Type[ConverterPlugin]] = []
    skipped: List[PluginDiscoverySkip] = []

    for module_name in sorted(_iter_plugin_module_names()):
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            skipped.append(
                PluginDiscoverySkip(
                    module_name=module_name,
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if (
                isinstance(attribute, type)
                and issubclass(attribute, ConverterPlugin)
                and attribute is not ConverterPlugin
            ):
                discovered.append(attribute)

    return PluginDiscoveryResult(
        plugin_classes=discovered,
        skipped_plugins=skipped,
    )


def discover_plugin_classes() -> List[Type[ConverterPlugin]]:
    return discover_plugins().plugin_classes
