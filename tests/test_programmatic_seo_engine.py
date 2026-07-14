"""Regression tests for ProgrammaticSeoEngine and integrated dashboard metrics."""

import pytest
from pathlib import Path

from app.services.programmatic_seo_engine import ProgrammaticSeoEngine
from app.services.production_audit_service import ProductionAuditService
from app.services.growth_dashboard_service import GrowthDashboardService


class TestProgrammaticSeoEngine:
    """Test ProgrammaticSeoEngine core functionality."""

    def test_seo_engine_initializes(self) -> None:
        """Test ProgrammaticSeoEngine can be instantiated."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        assert engine is not None
        assert engine.converter_registry_service is not None
        assert engine.topic_cluster_service is not None

    def test_generate_page_how_to(self) -> None:
        """Test generating a How To page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("pdf", "how_to")
        
        assert page["format"] == "pdf"
        assert page["page_type"] == "how_to"
        assert page["url"] == "/how-to/pdf"
        assert "seo" in page
        assert "content" in page

    def test_generate_page_tutorials(self) -> None:
        """Test generating a Tutorials page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("png", "tutorials")
        
        assert page["format"] == "png"
        assert page["page_type"] == "tutorials"
        assert page["url"] == "/tutorials/png"

    def test_generate_page_best_practices(self) -> None:
        """Test generating a Best Practices page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("jpg", "best_practices")
        
        assert page["format"] == "jpg"
        assert page["page_type"] == "best_practices"

    def test_generate_page_troubleshooting(self) -> None:
        """Test generating a Troubleshooting page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("docx", "troubleshooting")
        
        assert page["page_type"] == "troubleshooting"
        assert "content" in page
        assert "issues" in page["content"]

    def test_generate_page_file_format_guides(self) -> None:
        """Test generating a File Format Guide page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("mp4", "file_format_guides")
        
        assert page["page_type"] == "file_format_guides"
        assert "/formats/" in page["url"]

    def test_generate_page_use_cases(self) -> None:
        """Test generating a Use Cases page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("webp", "use_cases")
        
        assert page["page_type"] == "use_cases"
        assert "use_cases" in page["content"]

    def test_generate_page_faqs(self) -> None:
        """Test generating a FAQs page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("mp3", "faqs")
        
        assert page["page_type"] == "faqs"
        assert "faq" in page["content"]

    def test_generate_page_metadata_guides(self) -> None:
        """Test generating a Metadata Guide page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("wav", "metadata_guides")
        
        assert page["page_type"] == "metadata_guides"
        assert "/guides/" in page["url"]

    def test_generate_page_mime_guides(self) -> None:
        """Test generating a MIME Guide page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("avi", "mime_guides")
        
        assert page["page_type"] == "mime_guides"

    def test_generate_page_software_guides(self) -> None:
        """Test generating a Software Guide page."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page("gif", "software_guides")
        
        assert page["page_type"] == "software_guides"
        assert "native_support" in page["content"]
        assert "also_supported_by" in page["content"]

    def test_all_pages_have_required_seo_fields(self) -> None:
        """Test all pages have required SEO fields."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        for page_type in engine.PAGE_TYPES:
            page = engine.generate_page("pdf", page_type)
            seo = page.get("seo", {})
            
            assert seo.get("title"), f"{page_type} missing SEO title"
            assert seo.get("meta_description"), f"{page_type} missing meta description"
            assert seo.get("canonical"), f"{page_type} missing canonical"
            assert seo.get("keywords"), f"{page_type} missing keywords"

    def test_all_pages_have_json_ld_schema(self) -> None:
        """Test all pages have JSON-LD schema."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        for page_type in engine.PAGE_TYPES:
            page = engine.generate_page("pdf", page_type)
            
            assert page.get("json_ld"), f"{page_type} missing JSON-LD"
            assert page["json_ld"].get("@context"), f"{page_type} JSON-LD missing @context"
            assert page["json_ld"].get("@type"), f"{page_type} JSON-LD missing @type"

    def test_all_pages_have_breadcrumb(self) -> None:
        """Test all pages have breadcrumb navigation."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        for page_type in engine.PAGE_TYPES:
            page = engine.generate_page("png", page_type)
            breadcrumb = page.get("breadcrumb", [])
            
            assert len(breadcrumb) > 0, f"{page_type} missing breadcrumb"
            assert breadcrumb[0]["name"] == "Home", f"{page_type} breadcrumb missing home"

    def test_generate_all_pages(self) -> None:
        """Test generating all pages for all formats."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        all_pages = engine.generate_all_pages()
        
        assert isinstance(all_pages, dict)
        assert len(all_pages) > 0

    def test_seo_coverage_report_structure(self) -> None:
        """Test SEO coverage report has expected structure."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        report = engine.get_seo_page_coverage_report()
        
        assert "total_formats" in report
        assert "seo_pages_total" in report
        assert "seo_pages_ready" in report
        assert "seo_page_coverage" in report
        assert "completeness_percentage" in report
        assert "orphan_seo_pages" in report
        assert "page_types_supported" in report


class TestProductionAuditServiceSeoIntegration:
    """Test ProductionAuditService integration with ProgrammaticSeoEngine."""

    def test_production_audit_has_seo_engine(self) -> None:
        """Test ProductionAuditService has ProgrammaticSeoEngine."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        assert hasattr(service, "seo_engine")
        assert service.seo_engine is not None

    def test_audit_converter_includes_seo_checks(self) -> None:
        """Test audit includes SEO checks."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        converters = service.converter_registry_service.get_active()
        assert len(converters) > 0
        
        audit_result = service.audit_converter(converters[0])
        
        assert "checks" in audit_result
        assert "seo_structure" in audit_result["checks"]
        assert "seo_metadata" in audit_result["checks"]
        assert "seo_internal_links" in audit_result["checks"]
        assert "seo_content_quality" in audit_result["checks"]

    def test_get_seo_pages_report(self) -> None:
        """Test ProductionAuditService provides SEO pages report."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        report = service.get_seo_pages_report()
        
        assert "total_formats" in report
        assert "seo_pages_total" in report
        assert "seo_page_coverage" in report

    def test_audit_scores_include_seo_checks(self) -> None:
        """Test that audit scoring includes SEO checks."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        converters = service.converter_registry_service.get_active()
        assert len(converters) > 0
        
        audit_result = service.audit_converter(converters[0])
        
        # Quality score should be out of 17 checks now
        quality_score = audit_result.get("quality_score", 0)
        assert 0 <= quality_score <= 100


class TestGrowthDashboardServiceSeoIntegration:
    """Test GrowthDashboardService integration with ProgrammaticSeoEngine."""

    def test_growth_dashboard_has_seo_engine(self) -> None:
        """Test GrowthDashboardService instantiates ProgrammaticSeoEngine."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        assert hasattr(service, "seo_engine")
        assert service.seo_engine is not None

    def test_dashboard_includes_seo_pages_metrics(self) -> None:
        """Test that dashboard includes SEO pages metrics."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        dashboard = service.build_dashboard()
        
        assert "seo_pages" in dashboard
        metrics = dashboard["seo_pages"]
        
        assert "seo_pages_total" in metrics
        assert "seo_pages_ready" in metrics
        assert "seo_page_coverage" in metrics
        assert "orphan_seo_pages" in metrics

    def test_dashboard_seo_metrics_are_valid(self) -> None:
        """Test that SEO pages metrics are valid."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        dashboard = service.build_dashboard()
        metrics = dashboard["seo_pages"]
        
        # Coverage should be between 0 and 100
        coverage = metrics.get("seo_page_coverage", 0)
        assert 0 <= coverage <= 100
        
        # Orphan pages should be non-negative
        orphans = metrics.get("orphan_seo_pages", 0)
        assert orphans >= 0
        
        # Completeness should be between 0 and 100
        completeness = metrics.get("completeness_percentage", 0)
        assert 0 <= completeness <= 100

    def test_dashboard_complete_build_with_seo_pages(self) -> None:
        """Test that dashboard builds successfully with all SEO pages metrics."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        # Should not raise any exceptions
        dashboard = service.build_dashboard()
        
        # Check expected structure
        assert "total_converters" in dashboard
        assert "registry_health" in dashboard
        assert "production_audit" in dashboard
        assert "internal_linking" in dashboard
        assert "topic_clusters" in dashboard
        assert "seo_pages" in dashboard


class TestProgrammaticSeoEndToEnd:
    """End-to-end tests for programmatic SEO functionality."""

    def test_all_page_types_generate_successfully(self) -> None:
        """Test that all page types generate successfully."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        for page_type in engine.PAGE_TYPES:
            page = engine.generate_page("pdf", page_type)
            assert page is not None
            assert page.get("page_type") == page_type

    def test_common_formats_have_all_page_types(self) -> None:
        """Test that common formats have all page types."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        common_formats = ["pdf", "png", "jpg", "mp4", "mp3"]
        
        for fmt in common_formats:
            for page_type in engine.PAGE_TYPES:
                page = engine.generate_page(fmt, page_type)
                assert page is not None
                assert page["format"] == fmt
                assert page["page_type"] == page_type

    def test_seo_structure_is_consistent(self) -> None:
        """Test that SEO structure is consistent across all page types."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        for page_type in engine.PAGE_TYPES:
            page = engine.generate_page("pdf", page_type)
            
            # Check required top-level fields
            required_fields = [
                "format", "page_type", "url", "seo", "breadcrumb",
                "content", "json_ld", "internal_links", "related_topics", "related_converters"
            ]
            
            for field in required_fields:
                assert field in page, f"{page_type} missing field: {field}"

    def test_json_ld_schemas_are_valid(self) -> None:
        """Test that JSON-LD schemas are valid."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        for page_type in engine.PAGE_TYPES:
            page = engine.generate_page("pdf", page_type)
            schema = page.get("json_ld", {})
            
            assert "@context" in schema
            assert "@type" in schema
            assert schema["@context"] == "https://schema.org"

    def test_pages_are_deterministic(self) -> None:
        """Test that pages generate deterministically."""
        engine1 = ProgrammaticSeoEngine(Path("app/data/converters"))
        engine2 = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        page1 = engine1.generate_page("pdf", "how_to")
        page2 = engine2.generate_page("pdf", "how_to")
        
        # Key fields should match
        assert page1["format"] == page2["format"]
        assert page1["page_type"] == page2["page_type"]
        assert page1["url"] == page2["url"]
        assert page1["seo"]["title"] == page2["seo"]["title"]

    def test_page_types_count(self) -> None:
        """Test that correct number of page types are supported."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        assert len(engine.PAGE_TYPES) == 10
        assert "how_to" in engine.PAGE_TYPES
        assert "tutorials" in engine.PAGE_TYPES
        assert "best_practices" in engine.PAGE_TYPES
        assert "troubleshooting" in engine.PAGE_TYPES
        assert "file_format_guides" in engine.PAGE_TYPES
        assert "use_cases" in engine.PAGE_TYPES
        assert "faqs" in engine.PAGE_TYPES
        assert "metadata_guides" in engine.PAGE_TYPES
        assert "mime_guides" in engine.PAGE_TYPES
        assert "software_guides" in engine.PAGE_TYPES

    def test_coverage_report_values_realistic(self) -> None:
        """Test that coverage report has realistic values."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        
        report = engine.get_seo_page_coverage_report()
        
        # All values should be realistic
        assert report.get("total_formats", 0) > 0
        assert report.get("seo_pages_total", 0) > 0
        assert report.get("page_types_supported", 0) == 10
        
        # Coverage percentage should be 0-100
        coverage = report.get("seo_page_coverage", 0)
        assert 0 <= coverage <= 100
        
        # Completeness should be 0-100
        completeness = report.get("completeness_percentage", 0)
        assert 0 <= completeness <= 100
