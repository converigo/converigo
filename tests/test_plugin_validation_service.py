"""
Tests for PluginValidationService

Validates that the validation framework correctly detects:
- Duplicate slugs
- Missing metadata
- Invalid categories
- Plugin availability
- Route rendering capability
- SEO generation
- Hub inclusion
- Recommendation participation
- Sitemap inclusion
"""

import json
from pathlib import Path

import pytest

from app.services.converter_data_service import ConverterDataService
from app.services.plugin_validation_service import PluginValidationService, ValidationResult


def _write_converter(
    path: Path,
    *,
    slug: str,
    category: str = "image",
    popular: bool = True,
    featured: bool = False,
    source: str | None = None,
    target: str | None = None,
    active: bool = True,
    related_slugs: list[str] | None = None,
) -> None:
    """Helper to write converter JSON fixture."""
    payload = {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "description": f"{slug} converter",
        "category": category,
        "popular": popular,
        "featured": featured,
        "source": source or slug.split("-to-")[0],
        "target": target or slug.split("-to-")[1] if "-to-" in slug else slug,
        "active": active,
    }
    if related_slugs is not None:
        payload["related_tools"] = [{"slug": related_slug} for related_slug in related_slugs]
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestValidationResult:
    """Test ValidationResult container."""

    def test_validation_result_is_valid_when_no_errors(self) -> None:
        result = ValidationResult("test-slug")
        assert result.is_valid()

    def test_validation_result_is_invalid_when_errors_present(self) -> None:
        result = ValidationResult("test-slug")
        result.add_error("Test error")
        assert not result.is_valid()

    def test_validation_result_tracks_checks(self) -> None:
        result = ValidationResult("test-slug")
        result.add_check("test_check", True)
        assert result.checks["test_check"] is True

    def test_validation_result_to_dict(self) -> None:
        result = ValidationResult("test-slug")
        result.add_check("test_check", True)
        result.add_warning("Test warning")
        data = result.to_dict()
        assert data["slug"] == "test-slug"
        assert data["valid"] is True
        assert "test_check" in data["checks"]


class TestPluginValidationService:
    """Test PluginValidationService."""

    def test_validate_json_valid_converter(self, tmp_path: Path) -> None:
        """Test JSON validation for valid converter."""
        data_dir = tmp_path
        _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png", category="image")

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("json_valid") is True

    def test_validate_json_missing_file(self, tmp_path: Path) -> None:
        """Test JSON validation detects missing file."""
        data_dir = tmp_path

        service = PluginValidationService(data_dir)
        result = service.validate_converter("nonexistent")

        assert result.checks.get("json_valid") is False
        assert any("not found" in error.lower() for error in result.errors)

    def test_validate_metadata_valid(self, tmp_path: Path) -> None:
        """Test metadata validation for valid converter."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            category="image",
            source="jpg",
            target="png",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("metadata_valid") is True

    def test_validate_metadata_missing_slug(self, tmp_path: Path) -> None:
        """Test metadata validation auto-derives slug from filename."""
        data_dir = tmp_path
        # Write JSON without slug - ConverterDataService will auto-derive from filename
        payload = {
            "title": "Test",
            "category": "image",
            "source": "jpg",
            "target": "png",
        }
        (data_dir / "jpg-to-png.json").write_text(json.dumps(payload), encoding="utf-8")

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        # Should pass because slug is auto-derived from filename
        assert result.checks.get("metadata_valid") is True

    def test_validate_metadata_missing_source(self, tmp_path: Path) -> None:
        """Test metadata validation auto-derives source from slug."""
        data_dir = tmp_path
        # Write JSON without source - ConverterDataService will auto-derive from slug
        payload = {
            "slug": "jpg-to-png",
            "title": "Test",
            "category": "image",
            "target": "png",
        }
        (data_dir / "jpg-to-png.json").write_text(json.dumps(payload), encoding="utf-8")

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        # Should pass because source is auto-derived from slug
        assert result.checks.get("metadata_valid") is True

    def test_validate_metadata_missing_target(self, tmp_path: Path) -> None:
        """Test metadata validation auto-derives target from slug."""
        data_dir = tmp_path
        # Write JSON without target - ConverterDataService will auto-derive from slug
        payload = {
            "slug": "jpg-to-png",
            "title": "Test",
            "category": "image",
            "source": "jpg",
        }
        (data_dir / "jpg-to-png.json").write_text(json.dumps(payload), encoding="utf-8")

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        # Should pass because target is auto-derived from slug
        assert result.checks.get("metadata_valid") is True

    def test_validate_metadata_invalid_category(self, tmp_path: Path) -> None:
        """Test metadata validation warns about invalid category."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            category="invalid-category",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert any("category" in warning.lower() for warning in result.warnings)

    def test_validate_plugin_exists(self, tmp_path: Path) -> None:
        """Test plugin validation for existing plugin."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            source="jpg",
            target="png",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("plugin_exists") is True

    def test_validate_plugin_missing(self, tmp_path: Path) -> None:
        """Test plugin validation detects missing plugin."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "nonexistent-to-format.json",
            slug="nonexistent-to-format",
            source="nonexistent",
            target="format",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("nonexistent-to-format")

        assert result.checks.get("plugin_exists") is False
        assert any("plugin" in error.lower() for error in result.errors)

    def test_validate_route_valid(self, tmp_path: Path) -> None:
        """Test route validation for valid converter."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            source="jpg",
            target="png",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("route_valid") is True

    def test_validate_route_missing_source(self, tmp_path: Path) -> None:
        """Test route validation auto-derives source from slug."""
        data_dir = tmp_path
        payload = {
            "slug": "jpg-to-png",
            "title": "Test",
            "category": "image",
            # Missing source
            "target": "png",
        }
        (data_dir / "jpg-to-png.json").write_text(json.dumps(payload), encoding="utf-8")

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        # Should pass because source is auto-derived from slug
        assert result.checks.get("route_valid") is True

    def test_validate_seo_valid(self, tmp_path: Path) -> None:
        """Test SEO validation for valid converter."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            source="jpg",
            target="png",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("seo_valid") is True

    def test_validate_sitemap_included(self, tmp_path: Path) -> None:
        """Test sitemap validation includes active converter."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            source="jpg",
            target="png",
            active=True,
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("sitemap_valid") is True

    def test_validate_recommendation_valid(self, tmp_path: Path) -> None:
        """Test recommendation validation."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            category="image",
            source="jpg",
            target="png",
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.checks.get("recommendation_valid") is True

    def test_check_duplicate_slugs_detects_duplicates(self, tmp_path: Path) -> None:
        """Test duplicate slug detection."""
        data_dir = tmp_path
        _write_converter(data_dir / "jpg-to-png-1.json", slug="jpg-to-png")
        _write_converter(data_dir / "jpg-to-png-2.json", slug="jpg-to-png")

        service = PluginValidationService(data_dir)
        duplicates = service.check_duplicate_slugs()

        assert "jpg-to-png" in duplicates

    def test_check_missing_plugins_detects_missing_plugins(self, tmp_path: Path) -> None:
        """Test missing plugin detection."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            source="jpg",
            target="png",
        )
        _write_converter(
            data_dir / "missing-plugin.json",
            slug="missing-plugin",
            source="nonexistent",
            target="format",
        )

        service = PluginValidationService(data_dir)
        missing = service.check_missing_plugins()

        assert "missing-plugin" in missing

    def test_validate_all_returns_results_for_all_converters(self, tmp_path: Path) -> None:
        """Test validate_all processes all active converters."""
        data_dir = tmp_path
        _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png")
        _write_converter(data_dir / "png-to-jpg.json", slug="png-to-jpg")
        _write_converter(
            data_dir / "inactive.json",
            slug="inactive-converter",
            active=False,
        )

        service = PluginValidationService(data_dir)
        results = service.validate_all()

        # Should include only active converters
        result_slugs = [r.slug for r in results]
        assert "jpg-to-png" in result_slugs
        assert "png-to-jpg" in result_slugs
        assert "inactive-converter" not in result_slugs

    def test_generate_report_includes_summary(self, tmp_path: Path) -> None:
        """Test report generation includes summary."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            source="jpg",
            target="png",
        )

        service = PluginValidationService(data_dir)
        report = service.generate_report()

        assert "summary" in report
        assert "total_converters" in report["summary"]
        assert "valid_converters" in report["summary"]
        assert "invalid_converters" in report["summary"]
        assert "validity_percentage" in report["summary"]

    def test_generate_report_includes_duplicate_check(self, tmp_path: Path) -> None:
        """Test report includes duplicate slug check."""
        data_dir = tmp_path
        _write_converter(data_dir / "jpg-to-png-1.json", slug="jpg-to-png")
        _write_converter(data_dir / "jpg-to-png-2.json", slug="jpg-to-png")

        service = PluginValidationService(data_dir)
        report = service.generate_report()

        assert "duplicate_slugs" in report
        assert "jpg-to-png" in report["duplicate_slugs"]

    def test_generate_report_includes_missing_plugins_check(self, tmp_path: Path) -> None:
        """Test report includes missing plugins check."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "missing-plugin.json",
            slug="missing-plugin",
            source="nonexistent",
            target="format",
        )

        service = PluginValidationService(data_dir)
        report = service.generate_report()

        assert "missing_plugins" in report
        assert "missing-plugin" in report["missing_plugins"]


class TestIntegrationWithExistingConverters:
    """Integration tests with real converter data."""

    def test_validate_existing_jpg_to_png(self, tmp_path: Path) -> None:
        """Test validation against actual jpg-to-png converter."""
        data_dir = tmp_path
        _write_converter(
            data_dir / "jpg-to-png.json",
            slug="jpg-to-png",
            category="image",
            popular=True,
            featured=False,
            source="jpg",
            target="png",
            related_slugs=["png-to-jpg"],
        )

        service = PluginValidationService(data_dir)
        result = service.validate_converter("jpg-to-png")

        assert result.is_valid()
        assert result.checks.get("json_valid") is True
        assert result.checks.get("metadata_valid") is True
        assert result.checks.get("route_valid") is True
        assert result.checks.get("seo_valid") is True

    def test_all_converters_pass_validation(self, tmp_path: Path) -> None:
        """Test that all properly configured converters pass validation."""
        data_dir = tmp_path
        converters = [
            ("jpg-to-png", "image", "jpg", "png"),
            ("png-to-jpg", "image", "png", "jpg"),
            ("pdf-to-jpg", "pdf", "pdf", "jpg"),
            ("jpg-to-pdf", "pdf", "jpg", "pdf"),
            ("mp4-to-mp3", "audio", "mp4", "mp3"),
        ]

        for slug, category, source, target in converters:
            _write_converter(
                data_dir / f"{slug}.json",
                slug=slug,
                category=category,
                source=source,
                target=target,
            )

        service = PluginValidationService(data_dir)
        results = service.validate_all()

        # All should be valid
        valid_results = [r for r in results if r.is_valid()]
        assert len(valid_results) == len(converters)

    def test_generate_report_shows_100_percent_validity(self, tmp_path: Path) -> None:
        """Test that proper converters generate 100% validity report."""
        data_dir = tmp_path
        _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png")
        _write_converter(data_dir / "png-to-jpg.json", slug="png-to-jpg")

        service = PluginValidationService(data_dir)
        report = service.generate_report()

        summary = report["summary"]
        assert summary["total_converters"] > 0
        assert summary["validity_percentage"] == 100.0
        assert summary["invalid_converters"] == 0
