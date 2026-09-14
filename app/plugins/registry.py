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

        # slug -> plugin
        self.by_slug: dict[str, object] = {}

        # slug -> [(source,target), ...]
        # Accumulated union of every pair claimed by every class that ever
        # registered this slug. Duplicate slugs make this wider than the
        # instance by_slug actually dispatches to, so it is a claims/history
        # index only and must NEVER be used to authorize a request.
        self.registered_keys: dict[str, list[tuple[str, str]]] = defaultdict(list)

        # slug -> {(source,target), ...} claimed by the winner in by_slug.
        # Guard authority for slug-aware resolution: it is written in the same
        # statement as by_slug, so the pair the guard accepts and the instance
        # that resolves can never disagree (see get_plugin).
        self.slug_winner_pairs: dict[str, set[tuple[str, str]]] = {}

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

            # Plugins may register fewer pairs than the naive source x target
            # cross product (see ConverterPlugin.registration_pairs), e.g.
            # format-preserving ops that only support same-format pairs.
            registration_pairs = plugin.registration_pairs()

            for key in registration_pairs:

                self.plugins[key] = plugin

        # Populate slug index
        slug = getattr(plugin, "slug", None)
        if slug:
            slug = slug.lower().strip()
            # by_slug is a single-winner index: the last class to register this
            # slug replaces the previous one, whose pairs stay in the union
            # index. Track the winner's own claim set in lockstep with that
            # assignment so the resolution guard below can never authorize a
            # pair the dispatched instance does not actually implement.
            self.by_slug[slug] = plugin
            self.slug_winner_pairs[slug] = set(plugin.registration_pairs())
            self.registered_keys[slug].extend(registration_pairs)

    def has_slug(self, slug: str) -> bool:
        """Return True when a plugin with the given slug is registered."""
        if not slug:
            return False
        return slug.lower().strip() in self.by_slug

    def get_plugin(
        self,
        source_format: str,
        target_format: str,
        slug: str | None = None,
    ):

        source = source_format.lower()
        target = target_format.lower()

        # Slug-aware resolution: the slug must map to a registered plugin and
        # the requested (source, target) pair must be one the *dispatched*
        # plugin itself declared. The accumulated union in registered_keys is
        # not consulted: with a duplicate slug it can advertise pairs that only
        # a shadowed class claimed, which would clear the guard here and then
        # blow up inside the winner at run time.
        if slug:
            slug = slug.lower().strip()
            plugin = self.by_slug.get(slug)
            if plugin is None:
                raise ValueError(
                    f"Operation '{slug}' is not registered (slug tidak tersedia)."
                )
            if (source, target) not in self.slug_winner_pairs.get(slug, set()):
                raise ValueError(
                    f"Operation '{slug}' does not support {source} -> {target}."
                )
            return plugin

        # Legacy pair-based resolution.
        key = (source, target)

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