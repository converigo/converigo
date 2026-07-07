from __future__ import annotations

from typing import Dict, List, Optional, Type

from app.engines.base_engine import BaseEngine
from app.plugins.base import ConverterPlugin


# ==========================================================
# ENGINE REGISTRY
# ==========================================================

class EngineRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseEngine]] = {}

    def register(self, engine: Type[BaseEngine]) -> None:
        self._registry[engine.ENGINE_NAME] = engine

    def get(self, name: str) -> Type[BaseEngine]:
        if name not in self._registry:
            raise ValueError(f"Engine '{name}' is not registered.")
        return self._registry[name]

    def list(self) -> List[str]:
        return sorted(self._registry.keys())


ENGINE_REGISTRY = EngineRegistry()


def register_engine(engine: Type[BaseEngine]) -> None:
    ENGINE_REGISTRY.register(engine)


# ==========================================================
# PLUGIN REGISTRY
# ==========================================================

class PluginRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Type[ConverterPlugin]] = {}

    def register(self, plugin: Type[ConverterPlugin]) -> None:
        self._registry[plugin.slug] = plugin

    def get(self, slug: str) -> Type[ConverterPlugin]:
        if slug not in self._registry:
            raise ValueError(f"Plugin '{slug}' is not registered.")
        return self._registry[slug]

    def discover(self) -> None:
        from app.plugins import discover_plugin_classes

        for plugin in discover_plugin_classes():
            self.register(plugin)

    def resolve(
        self,
        source_format: str,
        target_format: str,
    ) -> Type[ConverterPlugin]:

        source = source_format.lower().lstrip(".")
        target = target_format.lower().lstrip(".")

        for plugin in self._registry.values():
            if plugin.supports(source, target):
                return plugin

        raise ValueError(
            f"No plugin found for {source} -> {target}"
        )

    def list(self) -> List[str]:
        return sorted(self._registry.keys())


PLUGIN_REGISTRY = PluginRegistry()


# ==========================================================
# CONVERSION MANAGER
# ==========================================================

class ConversionManager:

    def __init__(self) -> None:

        if not PLUGIN_REGISTRY.list():
            PLUGIN_REGISTRY.discover()

    # ---------- Plugin ----------

    def create_converter(
        self,
        source_format: str,
        target_format: str,
    ) -> ConverterPlugin:

        plugin = PLUGIN_REGISTRY.resolve(
            source_format,
            target_format,
        )

        return plugin()

    # ---------- Engine ----------

    def create_engine(
        self,
        engine_name: str,
    ) -> BaseEngine:

        engine = ENGINE_REGISTRY.get(engine_name)

        return engine()

    # ---------- Utilities ----------

    def plugins(self) -> List[str]:
        return PLUGIN_REGISTRY.list()

    def engines(self) -> List[str]:
        return ENGINE_REGISTRY.list()