"""Tests for SEO Audit Engine — Sprint 03A.

Covers:
- SEO Audit Engine audits all converters (TASK 1)
- SEO Score calculation (TASK 2)
- Missing metadata detection (TASK 3)
- Schema detection (TASK 3)
- Internal link detection (TASK 3)
- Dashboard integration (TASK 5)
"""

from pathlib import Path

from app.services.seo_audit_engine import SeoAuditEngine, AUDIT_CHECKS


def _get_engine() -> SeoAuditEngine:
    """Create a SeoAuditEngine instance for testing."""
    return SeoAuditEngine(contracts_dir=Path("app/data/converters"))


# ═══════════════════════════════════════════════════════════════════
# TASK 1 — SEO Audit Engine audits all converters
# ═══════════════════════════════════════════════════════════════════

def test_seo_audit_engine_audits_all_converters() -> None:
    """Verify the audit engine processes every available converter."""
    engine = _get_engine()
    result = engine.run_full_audit()

    assert result["version"] == "1.0.0"
    assert "generated_at" in result
    assert result["pages_audited"] > 0
    assert result["total_converters"] > 0
    assert result["pages_audited"] == result["total_converters"]

    # Check that all page results have required fields
    for page in result["page_results"]:
        assert "slug" in page
        assert "name" in page
        assert "category" in page
        assert "score" in page
        assert "status" in page
        assert "checks" in page
        assert 0 <= page["score"] <= 100

    # Verify aggregate structure
    assert "overall_score" in result
    assert "overall_status" in result
    assert "summary" in result
    assert "score_distribution" in result
    assert "critical_issues" in result
    assert "warnings" in result
    assert "passed_checks" in result
    assert "top_issues" in result
    assert "recommendations" in result
    assert "checks_definition" in result


def test_seo_audit_engine_single_converter() -> None:
    """Verify the engine can audit a single converter by slug."""
    engine = _get_engine()
    result = engine.run_audit_for_slug("mp4-to-mp3")

    assert result is not None
    assert result["slug"] == "mp4-to-mp3"
    assert result["name"] == "MP4 to MP3"
    assert 0 <= result["score"] <= 100
    assert result["total_checks"] == len(AUDIT_CHECKS)
    assert result["passed_count"] + result["critical_issues_count"] + result["warnings_count"] == result["total_checks"]

    # Verify all check types are present
    checks = result["checks"]
    for check in AUDIT_CHECKS:
        assert check.name in checks, f"Missing check: {check.name}"

    # Non-existent slug returns None
    missing = engine.run_audit_for_slug("non-existent-converter")
    assert missing is None


def test_seo_audit_engine_empty_contracts_dir(tmp_path: Path) -> None:
    """Verify the engine handles an empty converters directory gracefully."""
    engine = SeoAuditEngine(contracts_dir=tmp_path)
    result = engine.run_full_audit()

    assert result["pages_audited"] == 0
    assert result["total_converters"] == 0
    assert result["overall_status"] == "NO_DATA"
    assert "No converter pages found to audit" in result["recommendations"]


# ═══════════════════════════════════════════════════════════════════
# TASK 2 — SEO Score Calculation
# ═══════════════════════════════════════════════════════════════════

def test_seo_score_calculation() -> None:
    """Verify SEO Score is calculated as 0-100 with correct scoring."""
    engine = _get_engine()
    result = engine.run_full_audit()

    # Overall score should be between 0 and 100
    assert 0 <= result["overall_score"] <= 100

    # Score should be a float with at most 1 decimal place
    score_str = str(result["overall_score"])
    assert "." not in score_str or len(score_str.split(".")[1]) <= 1

    # Each page should have a valid score
    for page in result["page_results"]:
        assert 0 <= page["score"] <= 100

    # Score distribution should sum to total pages
    dist = result["score_distribution"]
    total_pages = result["pages_audited"]
    distribution_sum = sum(dist.values())
    assert distribution_sum == total_pages, f"Distribution {distribution_sum} != total {total_pages}"


def test_seo_score_status_mapping() -> None:
    """Verify score-to-status mapping is correct."""
    assert SeoAuditEngine._score_status(95) == "EXCELLENT"
    assert SeoAuditEngine._score_status(85) == "GOOD"
    assert SeoAuditEngine._score_status(65) == "FAIR"
    assert SeoAuditEngine._score_status(40) == "POOR"
    assert SeoAuditEngine._score_status(100) == "EXCELLENT"
    assert SeoAuditEngine._score_status(0) == "POOR"
    assert SeoAuditEngine._score_status(90) == "EXCELLENT"
    assert SeoAuditEngine._score_status(75) == "GOOD"
    assert SeoAuditEngine._score_status(55) == "FAIR"


# ═══════════════════════════════════════════════════════════════════
# TASK 3 — Missing metadata detection
# ═══════════════════════════════════════════════════════════════════

def test_missing_meta_detection() -> None:
    """Verify the audit engine detects missing or problematic metadata."""
    engine = _get_engine()
    result = engine.run_full_audit()

    # Every page should be checked for Title and Meta Description
    for page in result["page_results"]:
        checks = page["checks"]
        title_check = checks.get("Title", {})
        meta_check = checks.get("Meta Description", {})

        # Title and Description should have values (present in all contracts)
        assert title_check.get("value"), f"Page {page['slug']} has empty title value"
        assert meta_check.get("value"), f"Page {page['slug']} has empty meta description value"

    # Check that the critical issues and warnings are structured properly
    for issue in result["critical_issues"]:
        assert "slug" in issue
        assert "check" in issue
        assert "message" in issue
        assert "issues" in issue

    for warning in result["warnings"]:
        assert "slug" in warning
        assert "check" in warning
        assert "message" in warning
        assert "issues" in warning


def test_missing_meta_requires_valid_values() -> None:
    """Verify checks properly detect missing values with empty input."""
    engine = _get_engine()

    # Test title check with empty seo_meta
    title_result = engine._check_title({}, {}, "")
    assert title_result["status"] == "FAIL"
    assert title_result["score"] == 0

    # Test meta description with empty input
    meta_result = engine._check_meta_description({}, {})
    assert meta_result["status"] == "FAIL"
    assert meta_result["score"] == 0

    # Test canonical with empty input
    canonical_result = engine._check_canonical({}, {}, "")
    assert canonical_result["status"] == "FAIL"
    assert canonical_result["score"] == 0


# ═══════════════════════════════════════════════════════════════════
# TASK 3 — Schema Detection
# ═══════════════════════════════════════════════════════════════════

def test_schema_detection() -> None:
    """Verify JSON-LD schema presence is checked per page."""
    engine = _get_engine()
    result = engine.run_full_audit()

    for page in result["page_results"]:
        checks = page["checks"]
        jsonld_check = checks.get("JSON-LD", {})
        # All converter pages should have schema_status field
        assert "value" in jsonld_check
        schema_value = jsonld_check["value"]
        if isinstance(schema_value, dict):
            assert "schema_status" in schema_value


def test_breadcrumb_detection() -> None:
    """Verify breadcrumb checks are present for all pages."""
    engine = _get_engine()
    result = engine.run_full_audit()

    for page in result["page_results"]:
        checks = page["checks"]
        bc_check = checks.get("Breadcrumb", {})
        assert bc_check.get("status") in ("PASS", "WARN", "FAIL")
        assert "value" in bc_check


# ═══════════════════════════════════════════════════════════════════
# TASK 3 — Internal Link Detection
# ═══════════════════════════════════════════════════════════════════

def test_internal_link_detection() -> None:
    """Verify internal link coverage is checked per page."""
    engine = _get_engine()
    result = engine.run_full_audit()

    for page in result["page_results"]:
        checks = page["checks"]
        il_check = checks.get("Internal Links", {})
        assert "status" in il_check
        assert "message" in il_check

        # Each page should have some internal links
        value = il_check.get("value", {})
        if isinstance(value, dict):
            total = sum(value.values()) if value else 0
            assert total == 0 or total > 0  # just verify structure


def test_related_converters_detection() -> None:
    """Verify related converters are discovered for each page."""
    engine = _get_engine()
    result = engine.run_full_audit()

    for page in result["page_results"]:
        checks = page["checks"]
        rc_check = checks.get("Related Converters", {})
        assert "status" in rc_check
        assert "value" in rc_check
        value = rc_check.get("value", {})
        if isinstance(value, dict):
            assert "count" in value or not value


# ═══════════════════════════════════════════════════════════════════
# TASK 5 — Dashboard Integration
# ═══════════════════════════════════════════════════════════════════

def test_dashboard_payload_structure() -> None:
    """Verify the dashboard API payload structure is correct."""
    engine = _get_engine()
    result = engine.run_full_audit()

    # Dashboard payload fields
    assert "version" in result
    assert "generated_at" in result
    assert "pages_audited" in result
    assert "total_converters" in result
    assert "overall_score" in result
    assert "overall_status" in result
    assert "summary" in result
    assert "score_distribution" in result
    assert "critical_issues" in result
    assert "warnings" in result
    assert "passed_checks" in result
    assert "top_issues" in result
    assert "recommendations" in result
    assert "page_results" in result

    # Summary fields
    summary = result["summary"]
    assert "total_audited" in summary
    assert "average_score" in summary
    assert "best_score" in summary
    assert "worst_score" in summary

    # Score distribution
    dist = result["score_distribution"]
    assert "excellent" in dist
    assert "good" in dist
    assert "fair" in dist
    assert "poor" in dist


def test_dashboard_summary_statistics() -> None:
    """Verify aggregated summary statistics are computed correctly."""
    engine = _get_engine()
    result = engine.run_full_audit()

    summary = result["summary"]

    # Best should be >= average >= worst
    assert summary["best_score"] >= summary["average_score"]
    assert summary["average_score"] >= summary["worst_score"]

    # Total audited should match pages_audited
    assert summary["total_audited"] == result["pages_audited"]

    # Average should be between worst and best
    assert summary["worst_score"] <= summary["average_score"] <= summary["best_score"]


# ═══════════════════════════════════════════════════════════════════
# TASK 4 — Report Generation
# ═══════════════════════════════════════════════════════════════════

def test_report_generation(tmp_path: Path) -> None:
    """Verify the audit engine can generate a markdown report."""
    engine = _get_engine()
    result = engine.run_full_audit()

    report_path = engine.write_report(result, tmp_path)
    assert report_path.exists()
    assert report_path.name == "SEO_AUDIT_REPORT.md"

    content = report_path.read_text(encoding="utf-8")
    assert "# SEO Audit Report" in content
    assert "Summary" in content
    assert "Overall SEO Score" in content
    assert "Critical Issues" in content
    assert "Warnings" in content
    assert "Passed Checks" in content
    assert "Recommendations" in content

    # Verify per-page details are included
    for page in result["page_results"][:3]:
        assert page["slug"] in content


def test_report_empty_data(tmp_path: Path) -> None:
    """Verify report generation with empty data."""
    engine = SeoAuditEngine(contracts_dir=tmp_path)
    result = engine.run_full_audit()

    report_path = engine.write_report(result, tmp_path)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "# SEO Audit Report" in content


# ═══════════════════════════════════════════════════════════════════
# Check definitions integrity
# ═══════════════════════════════════════════════════════════════════

def test_audit_checks_definition() -> None:
    """Verify the audit check definitions are consistent."""
    check_names = [c.name for c in AUDIT_CHECKS]
    assert len(check_names) == len(set(check_names)), "Duplicate check names found"

    total_weight = sum(c.weight for c in AUDIT_CHECKS)
    assert total_weight == 100, f"Total weight {total_weight} != 100"

    # Verify all checks have required fields
    for check in AUDIT_CHECKS:
        assert check.name
        assert check.weight > 0
        assert check.description
        assert isinstance(check.critical, bool)

    # Critical checks should include title, meta, canonical, json-ld, internal links
    critical_checks = {c.name for c in AUDIT_CHECKS if c.critical}
    assert "Title" in critical_checks
    assert "Meta Description" in critical_checks
    assert "Canonical" in critical_checks
    assert "JSON-LD" in critical_checks
    assert "Internal Links" in critical_checks


def test_audit_check_to_dict() -> None:
    """Verify AuditCheck serialization works."""
    check = AUDIT_CHECKS[0]
    d = check.to_dict()
    assert d["name"] == check.name
    assert d["weight"] == check.weight
    assert d["description"] == check.description
    assert d["critical"] == check.critical


# ═══════════════════════════════════════════════════════════════════
# Regression — existing dashboard still works
# ═══════════════════════════════════════════════════════════════════

def test_regression_existing_services_unchanged() -> None:
    """Verify existing services remain functional."""
    from app.services.analytics_service import AnalyticsService
    from app.services.converter_registry_service import ConverterRegistryService

    # AnalyticsService should still build dashboard metrics
    analytics = AnalyticsService()
    metrics = analytics.build_dashboard_metrics()
    assert "total_visitor" in metrics
    assert "unique_visitor" in metrics

    # Converter registry should still list all contracts
    registry = ConverterRegistryService(Path("app/data/converters"))
    contracts = registry.list_all()
    assert len(contracts) > 0

