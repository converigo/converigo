"""
Project : Converigo
Author  : Converigo Team
Version : 3.0.0

Plugin Validation Service

Validates converters across all integration points:
- Plugin discovery and registration
- JSON metadata structure and content
- Route rendering capability
- SEO metadata generation
- Hub category inclusion
- Recommendation engine participation
- Sitemap inclusion
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.plugins import discover_plugin_classes
from app.plugins.registry import PluginRegistry
from app.services.converter_data_service import ConverterDataService
from app.services.hub_service import HubService
from app.services.recommendation_service import RecommendationService
from app.services.seo_service import SeoService


class ValidationResult:
    """Container for validation results."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: dict[str, bool] = {}

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_check(self, check_name: str, passed: bool) -> None:
        self.checks[check_name] = passed

    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "valid": self.is_valid(),
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
        }


class PluginValidationService:
    """
    Validates converters across all integration points.

    Uses ConverterDataService as the single source of truth for metadata.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.converter_data_service = ConverterDataService(data_dir)
        self.hub_service = HubService(self.converter_data_service)
        self.recommendation_service = RecommendationService(self.converter_data_service)
        self.seo_service = SeoService(data_dir)
        self.plugin_registry = PluginRegistry()

    def validate_all(self) -> list[ValidationResult]:
        """Validate all active converters."""
        results = []
        converters = self.converter_data_service.list_active_converters()

        for converter in converters:
            slug = str(converter.get("slug", ""))
            if slug:
                result = self.validate_converter(slug)
                results.append(result)

        return results

    def validate_converter(self, slug: str) -> ValidationResult:
        """Validate a single converter across all integration points."""
        result = ValidationResult(slug)

        # Validate JSON
        self.validate_json(slug, result)

        # Validate metadata
        if result.is_valid():
            converter = self.converter_data_service.load_converter_by_slug(slug)
            self.validate_metadata(converter, result)

        # Validate plugin exists
        self.validate_plugin(slug, result)

        # Validate route can be rendered
        if result.is_valid():
            converter = self.converter_data_service.load_converter_by_slug(slug)
            self.validate_route(converter, result)

        # Validate SEO generation
        if result.is_valid():
            converter = self.converter_data_service.load_converter_by_slug(slug)
            self.validate_seo(converter, result)

        # Validate hub inclusion
        if result.is_valid():
            converter = self.converter_data_service.load_converter_by_slug(slug)
            self.validate_hub(converter, result)

        # Validate recommendation inclusion
        if result.is_valid():
            self.validate_recommendation(slug, result)

        # Validate sitemap inclusion
        if result.is_valid():
            self.validate_sitemap(slug, result)

        return result

    def validate_json(self, slug: str, result: ValidationResult) -> None:
        """Validate JSON file exists and is parseable."""
        check_name = "json_valid"
        try:
            converter = self.converter_data_service.load_converter_by_slug(slug)
            if not converter:
                result.add_error(f"JSON file for '{slug}' is empty or missing")
                result.add_check(check_name, False)
                return
            result.add_check(check_name, True)
        except FileNotFoundError:
            result.add_error(f"JSON file not found for converter: {slug}")
            result.add_check(check_name, False)
        except json.JSONDecodeError as e:
            result.add_error(f"JSON parsing error for '{slug}': {e}")
            result.add_check(check_name, False)
        except Exception as e:
            result.add_error(f"Unexpected error loading JSON for '{slug}': {e}")
            result.add_check(check_name, False)

    def validate_metadata(self, converter: dict[str, Any], result: ValidationResult) -> None:
        """Validate metadata fields are present and valid."""
        check_name = "metadata_valid"
        errors_count = 0

        # Validate slug
        slug = str(converter.get("slug", "")).strip()
        if not slug:
            result.add_error("Missing or empty 'slug' field")
            errors_count += 1

        # Validate source
        source = str(converter.get("source", "")).strip().lower()
        if not source:
            result.add_error("Missing or empty 'source' field")
            errors_count += 1

        # Validate target
        target = str(converter.get("target", "")).strip().lower()
        if not target:
            result.add_error("Missing or empty 'target' field")
            errors_count += 1

        # Validate title
        title = str(converter.get("title", "")).strip()
        if not title:
            result.add_warning("Missing or empty 'title' field (will be auto-generated)")

        # Validate category
        category = str(converter.get("category", "general")).strip()
        valid_categories = {"image", "pdf", "audio", "video", "document", "general"}
        if category.lower() not in valid_categories:
            result.add_warning(f"Unknown category '{category}' (valid: {valid_categories})")

        # Validate active flag
        active = converter.get("active", True)
        if not isinstance(active, bool):
            result.add_warning(f"'active' should be boolean, got {type(active).__name__}")

        result.add_check(check_name, errors_count == 0)

    def validate_plugin(self, slug: str, result: ValidationResult) -> None:
        """Validate that a plugin exists for the converter."""
        check_name = "plugin_exists"
        try:
            converter = self.converter_data_service.load_converter_by_slug(slug)
            source = str(converter.get("source", "")).strip()
            target = str(converter.get("target", "")).strip()

            if not source or not target:
                result.add_error("Cannot validate plugin without source and target")
                result.add_check(check_name, False)
                return

            try:
                plugin = self.plugin_registry.get_plugin(source, target)
                if plugin:
                    result.add_check(check_name, True)
                else:
                    result.add_error(f"Plugin not found for {source} -> {target}")
                    result.add_check(check_name, False)
            except ValueError as e:
                result.add_error(f"Plugin lookup failed: {e}")
                result.add_check(check_name, False)

        except Exception as e:
            result.add_error(f"Error validating plugin: {e}")
            result.add_check(check_name, False)

    def validate_route(self, converter: dict[str, Any], result: ValidationResult) -> None:
        """Validate that route can be rendered without errors."""
        check_name = "route_valid"
        try:
            # Check critical fields for route rendering
            slug = str(converter.get("slug", "")).strip()
            title = converter.get("title") or converter.get("slug", "").replace("-", " ").title()
            category = converter.get("category", "general")

            if not slug:
                result.add_error("Cannot render route without slug")
                result.add_check(check_name, False)
                return

            # Route rendering requires basic fields
            source = converter.get("source", "").strip()
            target = converter.get("target", "").strip()

            if not source or not target:
                result.add_error("Route requires both source and target formats")
                result.add_check(check_name, False)
                return

            result.add_check(check_name, True)

        except Exception as e:
            result.add_error(f"Error validating route: {e}")
            result.add_check(check_name, False)

    def validate_seo(self, converter: dict[str, Any], result: ValidationResult) -> None:
        """Validate that SEO metadata can be generated."""
        check_name = "seo_valid"
        try:
            # Mock request object for SEO service
            class MockRequest:
                pass

            request = MockRequest()

            seo_data = self.seo_service.build_tool_meta(request, converter)

            if not seo_data:
                result.add_error("SEO metadata generation returned empty result")
                result.add_check(check_name, False)
                return

            # Validate critical SEO fields
            required_fields = ["title", "description", "canonical"]
            missing_fields = [f for f in required_fields if not seo_data.get(f)]

            if missing_fields:
                result.add_error(f"SEO missing required fields: {missing_fields}")
                result.add_check(check_name, False)
                return

            result.add_check(check_name, True)

        except Exception as e:
            result.add_error(f"Error validating SEO: {e}")
            result.add_check(check_name, False)

    def validate_hub(self, converter: dict[str, Any], result: ValidationResult) -> None:
        """Validate that converter is included in its hub."""
        check_name = "hub_valid"
        try:
            slug = str(converter.get("slug", "")).strip()

            # Get all hub definitions
            hub_defs = self.hub_service.get_hub_definitions()

            # Check which hubs include this converter
            matching_hubs = []
            for hub in hub_defs:
                hub_slug = hub.get("slug", "")
                # Use get_hub_page_data to get all matching converters for hub
                try:
                    hub_data = self.hub_service.get_hub_page_data(hub_slug)
                    all_hub_converters = hub_data.get("all_converters", [])
                    hub_slugs = [str(c.get("slug", "")) for c in all_hub_converters]
                    if slug in hub_slugs:
                        matching_hubs.append(hub_slug)
                except Exception:
                    pass

            if not matching_hubs:
                result.add_warning(f"Converter '{slug}' not included in any hub")
                result.add_check(check_name, True)  # Soft warning - hub inclusion is optional
                return

            result.add_check(check_name, True)

        except Exception as e:
            result.add_warning(f"Error validating hub inclusion: {e}")
            result.add_check(check_name, True)  # Soft fail - hub is nice-to-have

    def validate_recommendation(self, slug: str, result: ValidationResult) -> None:
        """Validate that converter is included in recommendations."""
        check_name = "recommendation_valid"
        try:
            # Check that converter can generate recommendations
            recommendations = self.recommendation_service.recommend_for_slug(slug)

            if not recommendations or all(not v for v in recommendations.values()):
                result.add_warning(f"Converter '{slug}' generates no recommendations")
                result.add_check(check_name, True)  # Soft warning
                return

            result.add_check(check_name, True)

        except Exception as e:
            result.add_warning(f"Error validating recommendation: {e}")
            result.add_check(check_name, True)  # Soft fail

    def validate_sitemap(self, slug: str, result: ValidationResult) -> None:
        """Validate that converter is included in sitemap."""
        check_name = "sitemap_valid"
        try:
            base_url = "https://converigo.com"
            entries = self.converter_data_service.sitemap_entries(base_url)

            # Check if converter slug appears in any sitemap entry
            entry_slugs = []
            for entry in entries:
                loc = entry.get("loc", "")
                # Extract slug from URL (both /tools/slug and /slug formats)
                if "/tools/" in loc:
                    entry_slugs.append(loc.split("/tools/")[-1])
                elif f"/{slug}" in loc:
                    entry_slugs.append(slug)

            if slug not in entry_slugs:
                result.add_error(f"Converter '{slug}' not found in sitemap entries")
                result.add_check(check_name, False)
                return

            result.add_check(check_name, True)

        except Exception as e:
            result.add_warning(f"Error validating sitemap: {e}")
            result.add_check(check_name, True)  # Soft fail

    def check_duplicate_slugs(self) -> list[str]:
        """Check for duplicate converter slugs."""
        converters = self.converter_data_service.list_all_converters()
        slugs = [str(c.get("slug", "")) for c in converters]
        seen = set()
        duplicates = []

        for slug in slugs:
            if slug in seen:
                duplicates.append(slug)
            seen.add(slug)

        return duplicates

    def check_missing_plugins(self) -> list[str]:
        """Check for converters without plugins."""
        missing = []
        converters = self.converter_data_service.list_active_converters()

        for converter in converters:
            slug = str(converter.get("slug", ""))
            source = str(converter.get("source", "")).strip()
            target = str(converter.get("target", "")).strip()

            if not source or not target:
                continue

            try:
                self.plugin_registry.get_plugin(source, target)
            except ValueError:
                missing.append(slug)

        return missing

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive validation report."""
        validation_results = self.validate_all()
        duplicate_slugs = self.check_duplicate_slugs()
        missing_plugins = self.check_missing_plugins()

        total_converters = len(validation_results)
        valid_converters = sum(1 for r in validation_results if r.is_valid())
        invalid_converters = total_converters - valid_converters

        # Aggregate check results
        check_summary = {}
        for result in validation_results:
            for check_name, passed in result.checks.items():
                if check_name not in check_summary:
                    check_summary[check_name] = {"passed": 0, "failed": 0}
                if passed:
                    check_summary[check_name]["passed"] += 1
                else:
                    check_summary[check_name]["failed"] += 1

        return {
            "summary": {
                "total_converters": total_converters,
                "valid_converters": valid_converters,
                "invalid_converters": invalid_converters,
                "validity_percentage": round(
                    (valid_converters / total_converters * 100) if total_converters > 0 else 0, 2
                ),
            },
            "duplicate_slugs": duplicate_slugs,
            "missing_plugins": missing_plugins,
            "check_summary": check_summary,
            "validation_results": [r.to_dict() for r in validation_results],
        }
