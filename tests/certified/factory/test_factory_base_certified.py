"""
PROJECT: CONVERIGO
TEST SUITE: Certified Factory Base Plugin (Jalur 2 / F0)

Certifies the factory scaffolding itself (app/factory/plugin_base.py):

- make_plugin_class() derives complete, honest metadata from slug+formats
  and rejects invalid specs (empty slug, unknown metadata keys).
- The inherited pipeline enforces the uniform factory contract at plugin
  level: supports() check -> single servable file -> non-empty output ->
  honest RuntimeError for unsupported input (the API maps this to 422
  UNSUPPORTED_CONVERSION).
- engine_hook-driven plugins behave exactly like hand-written plugins.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.factory import FactoryConversionPlugin, make_plugin_class


def _csv_to_any_hook(
    plugin: FactoryConversionPlugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    """Deterministic demo hook: writes one text file derived from the input."""
    output_path = working_root / f"{source_path.stem}.{target_format}"
    output_path.write_text(
        f"factory-hook:{plugin.slug}:{source_path.name}->{target_format}\n",
        encoding="utf-8",
    )
    return output_path


def _build_hook_plugin(**overrides):
    spec = {
        "slug": "csv-to-json",
        "source_formats": ["csv"],
        "target_formats": ["json"],
        "engine_hook": _csv_to_any_hook,
    }
    spec.update(overrides)
    return make_plugin_class(**spec)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.certified
def test_factory_make_plugin_class_derives_complete_metadata() -> None:
    cls = _build_hook_plugin()
    plugin = cls()
    assert plugin.slug == "csv-to-json"
    assert plugin.name == "CSV to JSON Converter"
    assert plugin.description == "Convert CSV files to JSON format."
    assert plugin.seo_title == "CSV to JSON Converter | Converigo"
    assert plugin.seo_description
    assert plugin.badge == "JSON Output"
    assert plugin.goal == "conversion"
    assert plugin.use_case
    assert isinstance(plugin.priority, int)
    assert plugin.source_formats == ["csv"]
    assert plugin.target_formats == ["json"]

    metadata = plugin.metadata()
    for key in ("slug", "name", "description", "category",
                "source_formats", "target_formats", "seo_title"):
        assert metadata[key], f"metadata '{key}' must be non-empty"
    # 'engine' is spec-owned (the base cannot know which engine a hook uses)
    assert metadata["engine"] == cls.engine


@pytest.mark.certified
def test_factory_make_plugin_class_metadata_overrides() -> None:
    cls = _build_hook_plugin(
        name="Custom CSV to JSON",
        category="spreadsheet",
        engine="spreadsheet",
        priority=75,
    )
    plugin = cls()
    assert plugin.name == "Custom CSV to JSON"
    assert plugin.category == "spreadsheet"
    assert plugin.engine == "spreadsheet"
    assert plugin.priority == 75
    assert cls.__name__ == "CsvToJsonPlugin"


@pytest.mark.certified
def test_factory_make_plugin_class_custom_class_name() -> None:
    cls = _build_hook_plugin(class_name="DemoPlugin")
    assert cls.__name__ == "DemoPlugin"
    assert issubclass(cls, FactoryConversionPlugin)


@pytest.mark.certified
@pytest.mark.parametrize(
    "bad_spec",
    [
        {"slug": ""},
        {"slug": "csv-to-json", "source_formats": []},
        {"slug": "csv-to-json", "source_formats": ["csv"], "target_formats": []},
    ],
)
def test_factory_make_plugin_class_rejects_invalid_specs(bad_spec: dict) -> None:
    base = {
        "source_formats": ["csv"],
        "target_formats": ["json"],
        "engine_hook": _csv_to_any_hook,
    }
    spec = {**base, **bad_spec}
    with pytest.raises(ValueError):
        make_plugin_class(**spec)


@pytest.mark.certified
def test_factory_make_plugin_class_rejects_unknown_metadata() -> None:
    with pytest.raises(TypeError):
        make_plugin_class(
            slug="csv-to-json",
            source_formats=["csv"],
            target_formats=["json"],
            engine_hook=_csv_to_any_hook,
            not_a_real_attribute=True,
        )


@pytest.mark.certified
def test_factory_engine_hook_convert_round_trip(tmp_path: Path) -> None:
    cls = _build_hook_plugin()
    plugin = cls()
    source = tmp_path / "input.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    output = asyncio.run(
        plugin.convert(
            source,
            "json",
            output_dir=tmp_path / "out",
            temp_dir=tmp_path / "tmp",
        )
    )
    assert output.is_file()
    assert output.name == "input.json"
    content = output.read_text(encoding="utf-8")
    assert "factory-hook:csv-to-json" in content


@pytest.mark.certified
def test_factory_plugin_honest_error_for_unsupported_input(tmp_path: Path) -> None:
    cls = _build_hook_plugin()
    plugin = cls()
    source = tmp_path / "input.txt"
    source.write_text("not a csv", encoding="utf-8")
    with pytest.raises(RuntimeError) as excinfo:
        asyncio.run(
            plugin.convert(
                source,
                "json",
                output_dir=tmp_path / "out",
                temp_dir=tmp_path / "tmp",
            )
        )
    message = str(excinfo.value)
    assert "csv-to-json" in message and "csv" in message and "json" in message


@pytest.mark.certified
def test_factory_plugin_rejects_empty_output(tmp_path: Path) -> None:
    def empty_hook(plugin, source_path, target_format, working_root):
        output_path = working_root / f"{source_path.stem}.{target_format}"
        output_path.write_bytes(b"")
        return output_path

    cls = make_plugin_class(
        slug="csv-to-json",
        source_formats=["csv"],
        target_formats=["json"],
        engine_hook=empty_hook,
    )
    plugin = cls()
    source = tmp_path / "input.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="empty output"):
        asyncio.run(
            plugin.convert(
                source,
                "json",
                output_dir=tmp_path / "out",
                temp_dir=tmp_path / "tmp",
            )
        )


@pytest.mark.certified
def test_factory_plugin_requires_single_servable_file(tmp_path: Path) -> None:
    def directory_hook(plugin, source_path, target_format, working_root):
        # A directory (what a raw archive-extract engine would return) is
        # NOT a servable file - the factory contract must reject it.
        output_dir = working_root / "result"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "inner.txt").write_text("x", encoding="utf-8")
        return output_dir

    cls = make_plugin_class(
        slug="csv-to-json",
        source_formats=["csv"],
        target_formats=["json"],
        engine_hook=directory_hook,
    )
    plugin = cls()
    source = tmp_path / "input.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="single servable"):
        asyncio.run(
            plugin.convert(
                source,
                "json",
                output_dir=tmp_path / "out",
                temp_dir=tmp_path / "tmp",
            )
        )

