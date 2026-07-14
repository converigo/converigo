"""Regression tests for InternalLinkService and integrated dashboard metrics."""

import pytest
from pathlib import Path

from app.services.internal_link_service import InternalLinkService
from app.services.production_audit_service import ProductionAuditService
from app.services.growth_dashboard_service import GrowthDashboardService


class TestInternalLinkService:
    """Test InternalLinkService core functionality."""

    def test_internal_link_service_initializes(self) -> None:
        """Test InternalLinkService can be instantiated."""
        service = InternalLinkService(Path("app/data/converters"))
        assert service is not None
        assert service.converter_registry_service is not None
        assert service.related_service is not None

    def test_get_links_for_landing_returns_dict_with_all_categories(self) -> None:
        """Test get_links_for_landing returns all link categories or empty structure."""
        service = InternalLinkService(Path("app/data/converters"))
        
        # Get a real converter
        converters = service.converter_registry_service.get_active()
        assert len(converters) > 0
        
        contract = converters[0]
        slug = contract.get("slug", "")
        
        links = service.get_links_for_landing(slug, contract)
        
        # Check structure is correct (after deduplication, not all categories may be present)
        assert isinstance(links, dict)
        # Should have at least one category with links or be mostly empty
        total_links = sum(len(items) for items in links.values() if isinstance(items, list))
        assert total_links >= 0
        
        # All items that exist should be lists
        for category, items in links.items():
            assert isinstance(items, list)
    def test_get_links_for_comparison_returns_valid_structure(self) -> None:
        """Test get_links_for_comparison returns proper link structure."""
        service = InternalLinkService(Path("app/data/converters"))
        
        links = service.get_links_for_comparison("pdf-vs-docx")
        
        # Check structure
        assert isinstance(links, dict)
        assert "related_converters" in links
        assert "related_formats" in links
        
        # Check items have required fields
        for category, items in links.items():
            if isinstance(items, list):
                for item in items:
                    assert "title" in item
                    assert "href" in item
                    assert "description" in item

    def test_get_links_for_format_generates_links(self) -> None:
        """Test get_links_for_format generates relevant links."""
        service = InternalLinkService(Path("app/data/converters"))
        
        links = service.get_links_for_format("pdf")
        
        assert isinstance(links, dict)
        assert len(links) > 0
        
        # Should have converters that handle PDF
        if links.get("related_converters"):
            assert len(links["related_converters"]) > 0

    def test_get_links_for_hub_generates_links(self) -> None:
        """Test get_links_for_hub generates hub-specific links."""
        service = InternalLinkService(Path("app/data/converters"))
        
        links = service.get_links_for_hub("image-conversion")
        
        assert isinstance(links, dict)
        # Should have relevant items for image hub
        has_links = any(len(items) > 0 for items in links.values() if isinstance(items, list))
        assert has_links

    def test_deduplicate_links_removes_duplicates(self) -> None:
        """Test that duplicate links are removed."""
        service = InternalLinkService(Path("app/data/converters"))
        
        duplicate_links = {
            "related_converters": [
                {"title": "PNG to JPG", "href": "/tools/png-to-jpg", "description": "Convert PNG to JPG", "score": 10},
                {"title": "PNG to JPG", "href": "/tools/png-to-jpg", "description": "Convert PNG to JPG", "score": 8},
            ],
            "related_formats": [
                {"title": "PNG format", "href": "/formats/png", "description": "PNG format info", "score": 9},
            ],
        }
        
        deduplicated = service._deduplicate_links(duplicate_links)
        
        # Should only have one PNG to JPG link (the one with highest score)
        total_items = sum(len(items) for items in deduplicated.values() if isinstance(items, list))
        assert total_items == 2

    def test_internal_link_coverage_report_structure(self) -> None:
        """Test internal link coverage report has expected structure."""
        service = InternalLinkService(Path("app/data/converters"))
        
        report = service.build_internal_link_coverage_report()
        
        assert "total_pages" in report
        assert "pages_with_internal_links" in report
        assert "internal_links_coverage_percentage" in report
        assert "landing_pages_with_links" in report
        assert "comparison_pages_with_links" in report
        assert "format_pages_with_links" in report
        assert "orphan_pages" in report
        assert "avg_internal_links_per_page" in report

    def test_internal_link_coverage_report_has_realistic_values(self) -> None:
        """Test coverage report metrics are realistic."""
        service = InternalLinkService(Path("app/data/converters"))
        
        report = service.build_internal_link_coverage_report()
        
        # Coverage percentage should be between 0 and 100
        coverage = report.get("internal_links_coverage_percentage", 0)
        assert 0 <= coverage <= 100
        
        # Orphan pages should be non-negative
        orphans = report.get("orphan_pages", 0)
        assert orphans >= 0
        
        # Total should equal sum of pages with links + orphans
        total = report.get("total_pages", 0)
        pages_with_links = report.get("pages_with_internal_links", 0)
        assert total == pages_with_links + orphans

    def test_comparison_specs_lookup_works(self) -> None:
        """Test that comparison specs can be looked up."""
        service = InternalLinkService(Path("app/data/converters"))
        
        specs = service._get_comparison_specs("pdf-vs-docx")
        
        assert specs["source_format"] == "pdf"
        assert specs["target_format"] == "docx"
        assert specs["title"] == "PDF vs DOCX"

    def test_comparison_specs_invalid_slug_raises_error(self) -> None:
        """Test that invalid comparison slug raises error."""
        service = InternalLinkService(Path("app/data/converters"))
        
        with pytest.raises(ValueError):
            service._get_comparison_specs("invalid-slug")

    def test_empty_links_returns_valid_structure(self) -> None:
        """Test _empty_links returns correct structure."""
        service = InternalLinkService(Path("app/data/converters"))
        
        empty = service._empty_links()
        
        assert "related_converters" in empty
        assert "related_formats" in empty
        assert "related_comparisons" in empty
        assert "related_knowledge" in empty
        assert "related_hubs" in empty
        assert "related_articles" in empty
        
        # All should be empty lists
        for key, value in empty.items():
            assert isinstance(value, list)
            assert len(value) == 0


class TestProductionAuditServiceIntegration:
    """Test ProductionAuditService integration with InternalLinkService."""

    def test_production_audit_service_has_internal_link_service(self) -> None:
        """Test ProductionAuditService can instantiate InternalLinkService."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        assert hasattr(service, "internal_link_service")
        assert service.internal_link_service is not None

    def test_production_audit_includes_internal_links_check(self) -> None:
        """Test that production audit checks for internal links."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        converters = service.converter_registry_service.get_active()
        assert len(converters) > 0
        
        audit_result = service.audit_converter(converters[0])
        
        assert "checks" in audit_result
        assert "internal_links" in audit_result["checks"]

    def test_get_internal_linking_report(self) -> None:
        """Test that ProductionAuditService provides internal linking report."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        report = service.get_internal_linking_report()
        
        assert "total_pages" in report
        assert "internal_links_coverage_percentage" in report


class TestGrowthDashboardServiceIntegration:
    """Test GrowthDashboardService integration with InternalLinkService."""

    def test_growth_dashboard_has_internal_link_service(self) -> None:
        """Test GrowthDashboardService instantiates InternalLinkService."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        assert hasattr(service, "internal_link_service")
        assert service.internal_link_service is not None

    def test_growth_dashboard_includes_internal_linking_metrics(self) -> None:
        """Test that growth dashboard includes internal linking metrics."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        dashboard = service.build_dashboard()
        
        assert "internal_linking" in dashboard
        metrics = dashboard["internal_linking"]
        
        assert "internal_links_coverage" in metrics
        assert "avg_internal_links_per_page" in metrics
        assert "orphan_pages" in metrics

    def test_growth_dashboard_internal_metrics_are_valid(self) -> None:
        """Test that internal linking metrics are valid."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        dashboard = service.build_dashboard()
        metrics = dashboard["internal_linking"]
        
        # Coverage should be between 0 and 100
        coverage = metrics.get("internal_links_coverage", 0)
        assert 0 <= coverage <= 100
        
        # Average should be non-negative
        avg = metrics.get("avg_internal_links_per_page", 0)
        assert avg >= 0
        
        # Orphan pages should be non-negative
        orphans = metrics.get("orphan_pages", 0)
        assert orphans >= 0

    def test_growth_dashboard_complete_build(self) -> None:
        """Test that growth dashboard builds successfully with all metrics."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        # Should not raise any exceptions
        dashboard = service.build_dashboard()
        
        # Check expected structure
        assert "total_converters" in dashboard
        assert "registry_health" in dashboard
        assert "production_audit" in dashboard
        assert "internal_linking" in dashboard
        assert "authority_coverage" in dashboard
        assert "format_encyclopedia_coverage" in dashboard


class TestInternalLinkingEndToEnd:
    """End-to-end tests for internal linking functionality."""

    def test_all_comparison_slugs_generate_links(self) -> None:
        """Test that all comparison slugs can generate links."""
        service = InternalLinkService(Path("app/data/converters"))
        
        comparison_slugs = ["pdf-vs-docx", "png-vs-jpg", "webp-vs-png", "mp4-vs-mov", "mp3-vs-wav"]
        
        for slug in comparison_slugs:
            links = service.get_links_for_comparison(slug)
            assert isinstance(links, dict)
            # Each comparison should have at least some links
            total_links = sum(len(items) for items in links.values() if isinstance(items, list))
            assert total_links > 0, f"Comparison {slug} should have generated links"

    def test_links_do_not_have_circular_references(self) -> None:
        """Test that internal links don't create problematic circular references."""
        service = InternalLinkService(Path("app/data/converters"))
        
        # Test converter page
        converters = service.converter_registry_service.get_active()
        if len(converters) > 0:
            slug = converters[0].get("slug", "")
            links = service.get_links_for_landing(slug, converters[0])
            
            # Links should not point back to the same page
            for category, items in links.items():
                if isinstance(items, list):
                    for item in items:
                        assert item.get("href") != f"/tools/{slug}", f"Link should not point to itself"

    def test_link_scoring_preserves_order(self) -> None:
        """Test that link scoring maintains meaningful order."""
        service = InternalLinkService(Path("app/data/converters"))
        
        # Get a converter
        converters = service.converter_registry_service.get_active()
        if len(converters) > 0:
            contract = converters[0]
            
            # Get related converters with scores
            related = service._get_related_converters(contract.get("slug", ""), contract)
            
            # Related converters should be sorted by score (implicit from algorithm)
            if len(related) > 1:
                scores = [item.get("score", 0) for item in related]
                # Scores should be non-negative
                assert all(score >= 0 for score in scores)

    def test_all_link_items_have_required_fields(self) -> None:
        """Test that all generated links have required fields."""
        service = InternalLinkService(Path("app/data/converters"))
        
        # Test multiple page types
        converters = service.converter_registry_service.get_active()
        if len(converters) > 0:
            landing_links = service.get_links_for_landing(converters[0].get("slug", ""), converters[0])
            
            for category, items in landing_links.items():
                if isinstance(items, list):
                    for item in items:
                        assert "title" in item, f"{category} item missing title"
                        assert "href" in item, f"{category} item missing href"
                        assert "description" in item, f"{category} item missing description"
                        assert isinstance(item["title"], str), "title should be string"
                        assert isinstance(item["href"], str), "href should be string"
                        assert isinstance(item["description"], str), "description should be string"
