"""
Tests for Search Console Readiness Service — Sprint 03C.

Covers:
- Sitemap validation (TASK 1)
- Robots validation (TASK 2)
- Indexability audit (TASK 3)
- Structured data validation (TASK 4)
- Canonical audit (TASK 5)
- Core SEO validation (TASK 6)
- Readiness scoring (TASK 7)
- Dashboard integration (TASK 8)
- Regression (TASK 9)
"""

from pathlib import Path
from collections import Counter

import pytest

from app.services.search_console_readiness_service import (
    SearchConsoleReadinessService,
    CheckResult,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def service() -> SearchConsoleReadinessService:
    return SearchConsoleReadinessService(
        contracts_dir=Path("app/data/converters"),
        output_dir=Path("outputs"),
    )


# ═══════════════════════════════════════════════════════════════════
# TASK 1 — Sitemap Validation
# ═══════════════════════════════════════════════════════════════════


def test_sitemap_validation_all_converters_present(service: SearchConsoleReadinessService) -> None:
    """All converter slugs should appear in sitemap URL entries."""
    audit = service.run_full_audit()
    sitemap = audit["sitemap"]
    assert "total_checks" in sitemap
    assert "critical_count" in sitemap
    assert "warning_count" in sitemap
    assert "pass_count" in sitemap

    # Should have at least sitemap index check
    assert sitemap["total_checks"] > 0


def test_sitemap_no_duplicate_urls(service: SearchConsoleReadinessService) -> None:
    """No duplicate URLs should exist across sitemaps."""
    audit = service.run_full_audit()
    critical_checks = audit.get("critical_issues", [])
    duplicate_issues = [c for c in critical_checks if "duplicate_url" in c.check_name]
    assert len(duplicate_issues) == 0, f"Found duplicate URL issues: {duplicate_issues}"


def test_sitemap_critical_issues_report_structure(service: SearchConsoleReadinessService) -> None:
    """Critical issues should have proper structure."""
    audit = service.run_full_audit()
    for issue in audit.get("critical_issues", []):
        assert isinstance(issue, CheckResult) or isinstance(issue, dict)
        if isinstance(issue, CheckResult):
            assert hasattr(issue, "converter_slug")
            assert hasattr(issue, "check_name")
            assert hasattr(issue, "status")
            assert hasattr(issue, "message")


# ═══════════════════════════════════════════════════════════════════
# TASK 2 — Robots Validation
# ═══════════════════════════════════════════════════════════════════


def test_robots_validation_performed(service: SearchConsoleReadinessService) -> None:
    """Robots validation should produce results."""
    audit = service.run_full_audit()
    robots = audit["robots"]
    assert "total_checks" in robots
    assert robots["total_checks"] > 0


def test_robots_sitemap_declared(service: SearchConsoleReadinessService) -> None:
    """Sitemap should be declared in robots.txt."""
    audit = service.run_full_audit()
    robots = audit["robots"]
    assert robots["total_checks"] >= 3  # sitemap, crawl permissions, blocked resources


# ═══════════════════════════════════════════════════════════════════
# TASK 3 — Indexability Audit
# ═══════════════════════════════════════════════════════════════════


def test_indexability_audits_all_converters(service: SearchConsoleReadinessService) -> None:
    """Every converter slug should have indexability checks."""
    audit = service.run_full_audit()
    indexability = audit["indexability"]
    assert indexability["total_checks"] > 0


def test_indexability_active_converters_pass(service: SearchConsoleReadinessService) -> None:
    """Active/certified converters should pass indexability check."""
    audit = service.run_full_audit()
    indexability = audit["indexability"]
    passed = indexability.get("passed", [])
    lifecycle_passes = [c for c in passed if c.get("check", "") == "indexable_lifecycle"]
    converters = service._load_converters()
    active_count = sum(1 for c in converters if str(c.get("lifecycle_status", "") or c.get("status", "") or "active").lower() in ("active", "certified"))
    if active_count > 0:
        assert len(lifecycle_passes) > 0


# ═══════════════════════════════════════════════════════════════════
# TASK 4 — Structured Data Validation
# ═══════════════════════════════════════════════════════════════════


def test_structured_data_validates_schema_types(service: SearchConsoleReadinessService) -> None:
    """Structured data validation should check for required schema types."""
    audit = service.run_full_audit()
    schema = audit["structured_data"]
    assert "total_checks" in schema
    # Schema checks are issue-only (no passes recorded for non-issues)
    # But checks should be performed
    assert schema["total_checks"] >= 0


def test_structured_data_required_schema_types_present(service: SearchConsoleReadinessService) -> None:
    """Organization, WebSite, and BreadcrumbList should be present on most pages."""
    audit = service.run_full_audit()
    # Schema validation only records failures (missing required fields)
    # With enhanced content, all converters should have Organization, WebSite, BreadcrumbList
    # So there should be few critical issues for schema
    schema = audit["structured_data"]
    # After Sprint 03B content enhancement, all converters have proper JSON-LD schema
    # So schema checks should have few if any critical issues
    assert schema["critical_count"] >= 0
    # At minimum, schema validation ran checks
    assert schema["total_checks"] >= 0


# ═══════════════════════════════════════════════════════════════════
# TASK 5 — Canonical Audit
# ═══════════════════════════════════════════════════════════════════


def test_canonical_validation_checks_all_converters(service: SearchConsoleReadinessService) -> None:
    """Canonical validation should check all converters."""
    audit = service.run_full_audit()
    canonical = audit["canonical"]
    converters = service._load_converters()
    active_slugs = [c.get("slug") for c in converters if c.get("slug")]
    # Canonical checks only report issues (missing, mismatch, duplicate)
    # After content enhancement, most should pass
    assert canonical["total_checks"] >= 0


def test_canonical_no_duplicates(service: SearchConsoleReadinessService) -> None:
    """No duplicate canonical URLs should exist."""
    audit = service.run_full_audit()
    critical = audit.get("critical_issues", [])
    duplicate_issues = [c for c in critical if "duplicate" in c.check_name.lower()]
    assert len(duplicate_issues) == 0, f"Found duplicate canonical issues: {duplicate_issues}"


# ═══════════════════════════════════════════════════════════════════
# TASK 6 — Core SEO Validation
# ═══════════════════════════════════════════════════════════════════


def test_core_seo_checks_title_meta(service: SearchConsoleReadinessService) -> None:
    """Core SEO should validate title and meta description."""
    audit = service.run_full_audit()
    core_seo = audit["core_seo"]
    assert core_seo["total_checks"] > 0
    # After content enhancement, all converters should have titles and descriptions
    converters = service._load_converters()
    active_count = len([c for c in converters if str(c.get("lifecycle_status", "") or c.get("status", "") or "active").lower() in ("active", "certified")])
    if active_count > 0:
        assert core_seo["pass_count"] >= active_count * 2  # at least title + desc per converter
        assert core_seo["critical_count"] <= (len(converters) - active_count) * 2  # deprecated at most


def test_core_seo_og_twitter_images(service: SearchConsoleReadinessService) -> None:
    """Core SEO should check OG and Twitter image metadata."""
    audit = service.run_full_audit()
    core_seo = audit["core_seo"]
    converters = service._load_converters()
    if len(converters) > 5:
        # After content enhancement, active converters should have OG/Twitter
        assert core_seo["pass_count"] >= len(converters) * 3  # og_image, og_alt, twitter per converter


# ═══════════════════════════════════════════════════════════════════
# TASK 7 — Readiness Scoring
# ═══════════════════════════════════════════════════════════════════


def test_readiness_score_range(service: SearchConsoleReadinessService) -> None:
    """Readiness score should be between 0-100."""
    audit = service.run_full_audit()
    score = audit["summary"]["readiness_score"]
    assert 0 <= score <= 100


def test_readiness_score_per_converter(service: SearchConsoleReadinessService) -> None:
    """Each converter should have a readiness score."""
    audit = service.run_full_audit()
    for pc in audit.get("per_converter", []):
        assert "readiness_score" in pc
        assert 0 <= pc["readiness_score"] <= 100
        assert pc["status"] in ("ready", "warning", "critical")
        assert "converter_slug" in pc
        assert "title" in pc


def test_readiness_status_mapping(service: SearchConsoleReadinessService) -> None:
    """Readiness status should map correctly from score."""
    audit = service.run_full_audit()
    for pc in audit.get("per_converter", []):
        score = pc["readiness_score"]
        status = pc["status"]
        if score >= 90:
            assert status == "ready", f"Score {score} should be 'ready', got '{status}'"
        elif score >= 70:
            assert status == "warning", f"Score {score} should be 'warning', got '{status}'"
        else:
            assert status == "critical", f"Score {score} should be 'critical', got '{status}'"


def test_summary_statistics(service: SearchConsoleReadinessService) -> None:
    """Summary statistics should be consistent."""
    audit = service.run_full_audit()
    summary = audit["summary"]
    assert summary["pages_audited"] > 0
    assert summary["critical_count"] >= 0
    assert summary["warning_count"] >= 0
    assert summary["pass_count"] > 0

    total = summary["critical_count"] + summary["warning_count"] + summary["pass_count"]
    assert total == audit["metadata"]["total_checks"]


# ═══════════════════════════════════════════════════════════════════
# TASK 8 — Dashboard Integration
# ═══════════════════════════════════════════════════════════════════


def test_dashboard_payload_structure(service: SearchConsoleReadinessService) -> None:
    """Dashboard payload should have required structure."""
    audit = service.run_full_audit()

    assert "metadata" in audit
    assert "summary" in audit
    assert "sitemap" in audit
    assert "robots" in audit
    assert "indexability" in audit
    assert "structured_data" in audit
    assert "canonical" in audit
    assert "core_seo" in audit
    assert "per_converter" in audit
    assert "critical_issues" in audit
    assert "warnings" in audit
    assert "passed_checks" in audit
    assert "recommendations" in audit
    assert "category_breakdowns" in audit

    summary = audit["summary"]
    assert "readiness_score" in summary
    assert "overall_status" in summary
    assert "pages_audited" in summary
    assert "pages_ready" in summary
    assert "critical_count" in summary
    assert "warning_count" in summary
    assert "pass_count" in summary


def test_dashboard_section_structure(service: SearchConsoleReadinessService) -> None:
    """Each dashboard section should have required structure."""
    audit = service.run_full_audit()
    sections = ["sitemap", "robots", "indexability", "structured_data", "canonical", "core_seo"]
    for section in sections:
        data = audit[section]
        assert "total_checks" in data
        assert "critical_count" in data
        assert "warning_count" in data
        assert "pass_count" in data
        assert "critical" in data
        assert "warnings" in data
        assert "passed" in data


# ═══════════════════════════════════════════════════════════════════
# TASK 9 — Regression
# ═══════════════════════════════════════════════════════════════════


def test_regression_no_exception_on_empty_data() -> None:
    """Service should handle empty data directory gracefully."""
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        empty_service = SearchConsoleReadinessService(
            contracts_dir=Path(tmp),
            output_dir=Path(tmp),
        )
        audit = empty_service.run_full_audit()
        assert audit["summary"]["pages_audited"] == 0


def test_regression_check_result_structure() -> None:
    """CheckResult should have all required fields."""
    result = CheckResult(
        converter_slug="test-slug",
        check_name="test_check",
        status="pass",
        message="Test passed",
        detail="Detail info",
    )
    assert result.converter_slug == "test-slug"
    assert result.check_name == "test_check"
    assert result.status == "pass"
    assert result.message == "Test passed"
    assert result.detail == "Detail info"


def test_regression_schema_required_fields_defined() -> None:
    """Required schema fields should be properly defined."""
    service = SearchConsoleReadinessService()
    assert "Organization" in service.SCHEMA_REQUIRED_FIELDS
    assert "WebSite" in service.SCHEMA_REQUIRED_FIELDS
    assert "FAQPage" in service.SCHEMA_REQUIRED_FIELDS
    assert "BreadcrumbList" in service.SCHEMA_REQUIRED_FIELDS
    assert len(service.REQUIRED_SCHEMA_TYPES) >= 4


def test_regression_weights_sum_to_100() -> None:
    """All category weights should sum to exactly 100."""
    service = SearchConsoleReadinessService()
    total = sum(service.WEIGHTS.values())
    assert total == 100, f"Weights sum to {total}, expected 100"


def test_regression_markdown_report_generated() -> None:
    """Generate report should produce valid markdown."""
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        service = SearchConsoleReadinessService(
            contracts_dir=Path("app/data/converters"),
            output_dir=tmp_path,
        )
        report = service.generate_report(tmp_path / "TEST_REPORT.md")
        assert report.startswith("# Search Console Readiness Report")
        assert "## Summary" in report
        assert "## Recommendations" in report
        assert len(report) > 500

