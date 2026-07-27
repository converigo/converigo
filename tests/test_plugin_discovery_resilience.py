from __future__ import annotations

from types import ModuleType
from typing import cast

from app.plugins import discover_plugins
from app.plugins.base import ConverterPlugin
from app.plugins.registry import PluginRegistry


class GoodPlugin(ConverterPlugin):
    slug = "good-plugin"
    name = "Good Plugin"
    description = "Valid plugin"
    category = "test"
    engine = "test"
    source_formats = ["src"]
    target_formats = ["dst"]

    async def convert(self, source_path, target_format):
        return source_path


class BrokenPlugin(ConverterPlugin):
    slug = "broken-plugin"
    name = "Broken Plugin"
    description = "Broken plugin"
    category = "test"
    engine = "test"
    source_formats = ["src"]
    target_formats = ["dst"]

    def __init__(self) -> None:
        raise RuntimeError("boom")

    async def convert(self, source_path, target_format):
        return source_path


def test_discover_plugins_skips_import_errors(monkeypatch):
    good_module = ModuleType("app.plugins.test.good")
    setattr(good_module, "GoodPlugin", GoodPlugin)

    monkeypatch.setattr(
        "app.plugins._iter_plugin_module_names",
        lambda: iter(["app.plugins.test.good", "app.plugins.test.bad"]),
    )

    def fake_import(module_name: str):
        if module_name == "app.plugins.test.bad":
            raise ImportError("No module named 'missing_pdf_dependency'")
        return good_module

    monkeypatch.setattr("app.plugins.importlib.import_module", fake_import)

    result = discover_plugins()

    assert [plugin.slug for plugin in result.plugin_classes] == ["good-plugin"]
    assert len(result.skipped_plugins) == 1
    assert result.skipped_plugins[0].module_name == "app.plugins.test.bad"
    assert "missing_pdf_dependency" in result.skipped_plugins[0].reason


def test_plugin_registry_continues_after_plugin_instantiation_failure(monkeypatch):
    monkeypatch.setattr(
        "app.plugins.registry.discover_plugins",
        lambda: cast(
            object,
            type(
                "DiscoveryResult",
                (),
                {
                    "plugin_classes": [GoodPlugin, BrokenPlugin],
                    "skipped_plugins": [],
                },
            )(),
        ),
    )

    registry = PluginRegistry()

    assert registry.get_plugin("src", "dst").slug == "good-plugin"
    assert registry.discovery_summary["loaded_plugins"] == ["good-plugin"]
    assert len(registry.discovery_summary["skipped_plugins"]) == 1
    assert registry.discovery_summary["skipped_plugins"][0]["plugin"].endswith("BrokenPlugin")
    assert "RuntimeError: boom" == registry.discovery_summary["skipped_plugins"][0]["reason"]