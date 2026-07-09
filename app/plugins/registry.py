"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.0.0

Automatic Plugin Registry
"""

from app.plugins import discover_plugin_classes


class PluginRegistry:

    def __init__(self):

        self.plugins = {}

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
                f"[OK] "
                f"{plugin.slug} "
                f"({plugin.source_formats} -> {plugin.target_formats})"
            )

        print("=" * 60)
        print(
            f"TOTAL PLUGINS : {len(plugin_classes)}"
        )
        print("=" * 60)

    def register(self, plugin):

        for source in plugin.source_formats:

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

            available = []

            for source, target in self.plugins.keys():

                available.append(
                    f"{source} -> {target}"
                )

            raise ValueError(

                "Converter "
                f"{source_format} -> {target_format} "
                "belum tersedia.\n\n"
                "Converter yang tersedia:\n"
                + "\n".join(available)

            )

        return self.plugins[key]


registry = PluginRegistry()