"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Plugin Registry

Converigo Core Architecture
"""

from __future__ import annotations

from collections import defaultdict
import logging

from app.plugins import discover_plugins

logger = logging.getLogger(__name__)


class PluginRegistry:

    def __init__(self):

        # (source,target) -> plugin
        self.plugins = {}

        # source -> [plugin]
        self.source_cache = defaultdict(list)
        self.discovery_summary = {
            "loaded_plugins": [],
            "skipped_plugins": [],
        }

        self.load_plugins()

    def load_plugins(self):

        discovery_result = discover_plugins()
        loaded_plugins = []
        skipped_plugins = [
            {
                "plugin": item.module_name,
                "reason": item.reason,
            }
            for item in discovery_result.skipped_plugins
        ]

        for plugin_class in discovery_result.plugin_classes:
            try:
                plugin = plugin_class()
                self.register(plugin)
                loaded_plugins.append(plugin.slug)
            except Exception as exc:
                skipped_plugins.append(
                    {
                        "plugin": f"{plugin_class.__module__}.{plugin_class.__name__}",
                        "reason": f"{type(exc).__name__}: {exc}",
                    }
                )

        self.discovery_summary = {
            "loaded_plugins": loaded_plugins,
            "skipped_plugins": skipped_plugins,
        }

        logger.info("%s", "=" * 60)
        logger.info("PLUGIN DISCOVERY")
        logger.info("%s", "=" * 60)

        for slug in loaded_plugins:
            logger.info("Loaded Plugin: %s", slug)

        for item in skipped_plugins:
            logger.warning(
                "Skipped Plugin: %s | Reason: %s",
                item["plugin"],
                item["reason"],
            )

        logger.info("%s", "=" * 60)
        logger.info("Loaded Plugin Count: %s", len(loaded_plugins))
        logger.info("Skipped Plugin Count: %s", len(skipped_plugins))
        logger.info("%s", "=" * 60)

    def register(self, plugin):

        for source in plugin.source_formats:

            self.source_cache[source.lower()].append(plugin)

            for target in plugin.target_formats:

                key = (
                    source.lower(),
                    target.lower(),
                )

                self.plugins[key] = plugin

    def get_plugin(
        self,
        source_format: str,
        target_format: str,
    ):

        key = (
            source_format.lower(),
            target_format.lower(),
        )

        if key not in self.plugins:

            raise ValueError(
                f"Converter {source_format} -> {target_format} tidak tersedia."
            )

        return self.plugins[key]

    def get_plugins_by_source(
        self,
        source_format: str,
    ):

        return self.source_cache.get(
            source_format.lower(),
            [],
        )

    def get_metadata(
        self,
        source_format: str,
    ):

        plugins = self.get_plugins_by_source(
            source_format
        )

        return [
            plugin.metadata()
            for plugin in plugins
        ]

    def get_best_plugin(
        self,
        source_format: str,
    ):

        plugins = self.get_plugins_by_source(
            source_format
        )

        if not plugins:

            return None

        return max(
            plugins,
            key=lambda plugin: (
                plugin.priority,
                plugin.quality,
                plugin.compatibility,
            ),
        )


registry = PluginRegistry()