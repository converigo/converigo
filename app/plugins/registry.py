"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Plugin Registry

Convertin Core Architecture
"""

from __future__ import annotations

from collections import defaultdict

from app.plugins import discover_plugin_classes


class PluginRegistry:

    def __init__(self):

        # (source,target) -> plugin
        self.plugins = {}

        # source -> [plugin]
        self.source_cache = defaultdict(list)

        self.load_plugins()

    def load_plugins(self):

        plugin_classes = discover_plugin_classes()

        print("=" * 60)
        print("PLUGIN DISCOVERY")
        print("=" * 60)

        for plugin_class in plugin_classes:

            plugin = plugin_class()

            self.register(plugin)

            print(
                f"[OK] {plugin.slug}"
            )

        print("=" * 60)
        print(
            f"TOTAL PLUGINS : {len(plugin_classes)}"
        )
        print("=" * 60)

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