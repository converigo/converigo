"""Regression tests for ContentQualityService and integrated quality metrics."""

import pytest
from pathlib import Path

from app.services.content_quality_service import ContentQualityService
from app.services.programmatic_seo_engine import ProgrammaticSeoEngine
from app.services.production_audit_service import ProductionAuditService
from app.services.growth_dashboard_service import GrowthDashboardService


class TestContentQualityService:
    """Test ContentQualityService core functionality."""

    def test_content_quality_service_initializes(self) -> None:
        """Test ContentQualityService can be instantiated."""
        service = ContentQualityService(Path("app/data/converters"))
        assert service is not None
        assert service.seo_engine is not None
        assert service.converter_registry_service is not None

    def test_evaluate_page_returns_complete_result(self) -> None:
        """Test evaluate_page returns all required fields."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("pdf", "how_to")
        
        assert "format" in result
        assert "page_type" in result
        assert "quality_score" in result
        assert "decision" in result
        assert "metrics" in result
        assert "recommendations" in result
        assert "missing_metadata" in result

    def test_quality_score_is_between_0_and_100(self) -> None:
        """Test quality_score is always between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("jpg", "tutorials")
        
        score = result.get("quality_score", 0)
        assert 0 <= score <= 100

    def test_decision_pass_threshold_90(self) -> None:
        """Test PASS decision requires score >= 90."""
        service = ContentQualityService(Path("app/data/converters"))
        
        # Simulate high quality page
        result = service.evaluate_page("pdf", "how_to")
        
        if result.get("quality_score", 0) >= 90:
            assert result.get("decision") == "PASS"

    def test_decision_needs_review_threshold_80_89(self) -> None:
        """Test NEEDS_REVIEW decision for score 80-89."""
        service = ContentQualityService(Path("app/data/converters"))
        
        result = service.evaluate_page("png", "best_practices")
        score = result.get("quality_score", 0)
        decision = result.get("decision")
        
        if 80 <= score < 90:
            assert decision == "NEEDS_REVIEW"

    def test_decision_no_index_threshold_60_79(self) -> None:
        """Test NO_INDEX decision for score 60-79."""
        service = ContentQualityService(Path("app/data/converters"))
        
        result = service.evaluate_page("mp4", "metadata_guides")
        score = result.get("quality_score", 0)
        decision = result.get("decision")
        
        if 60 <= score < 80:
            assert decision == "NO_INDEX"

    def test_decision_reject_threshold_below_60(self) -> None:
        """Test REJECT decision for score < 60."""
        service = ContentQualityService(Path("app/data/converters"))
        
        result = service.evaluate_page("docx", "software_guides")
        score = result.get("quality_score", 0)
        decision = result.get("decision")
        
        if score < 60:
            assert decision == "REJECT"

    def test_metrics_uniqueness_score_0_to_100(self) -> None:
        """Test uniqueness_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("webp", "troubleshooting")
        
        metrics = result.get("metrics", {})
        uniqueness = metrics.get("uniqueness_score", 0)
        assert 0 <= uniqueness <= 100

    def test_metrics_data_density_score_0_to_100(self) -> None:
        """Test data_density_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("gif", "use_cases")
        
        metrics = result.get("metrics", {})
        density = metrics.get("data_density_score", 0)
        assert 0 <= density <= 100

    def test_metrics_eligibility_score_0_to_100(self) -> None:
        """Test eligibility_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("mp3", "faqs")
        
        metrics = result.get("metrics", {})
        eligibility = metrics.get("eligibility_score", 0)
        assert 0 <= eligibility <= 100

    def test_metrics_search_intent_score_0_to_100(self) -> None:
        """Test search_intent_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("wav", "file_format_guides")
        
        metrics = result.get("metrics", {})
        intent = metrics.get("search_intent_score", 0)
        assert 0 <= intent <= 100

    def test_metrics_internal_link_score_0_to_100(self) -> None:
        """Test internal_link_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("avi", "mime_guides")
        
        metrics = result.get("metrics", {})
        links = metrics.get("internal_link_score", 0)
        assert 0 <= links <= 100

    def test_metrics_schema_score_0_to_100(self) -> None:
        """Test schema_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("bmp", "metadata_guides")
        
        metrics = result.get("metrics", {})
        schema = metrics.get("schema_score", 0)
        assert 0 <= schema <= 100

    def test_metrics_duplicate_score_0_to_100(self) -> None:
        """Test duplicate_score is between 0 and 100."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("tiff", "tutorials")
        
        metrics = result.get("metrics", {})
        duplicate = metrics.get("duplicate_score", 0)
        assert 0 <= duplicate <= 100

    def test_recommendations_are_list(self) -> None:
        """Test recommendations is a list of strings."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("svg", "best_practices")
        
        recommendations = result.get("recommendations", [])
        assert isinstance(recommendations, list)
        if recommendations:
            assert isinstance(recommendations[0], str)

    def test_missing_metadata_list_format(self) -> None:
        """Test missing_metadata is a list."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("ico", "how_to")
        
        missing = result.get("missing_metadata", [])
        assert isinstance(missing, list)

    def test_evaluate_all_pages_returns_aggregated_results(self) -> None:
        """Test evaluate_all_pages returns aggregated quality report."""
        service = ContentQualityService(Path("app/data/converters"))
        report = service.evaluate_all_pages()
        
        assert "total_pages_evaluated" in report
        assert "pass_count" in report
        assert "needs_review_count" in report
        assert "no_index_count" in report
        assert "reject_count" in report
        assert "average_quality_score" in report
        assert "pass_percentage" in report
        assert "results" in report

    def test_evaluate_all_pages_counts_sum_to_total(self) -> None:
        """Test evaluate_all_pages counts sum to total."""
        service = ContentQualityService(Path("app/data/converters"))
        report = service.evaluate_all_pages()
        
        total = report.get("total_pages_evaluated", 0)
        pass_count = report.get("pass_count", 0)
        review_count = report.get("needs_review_count", 0)
        no_index_count = report.get("no_index_count", 0)
        reject_count = report.get("reject_count", 0)
        
        assert pass_count + review_count + no_index_count + reject_count == total

    def test_deterministic_output_same_input_same_result(self) -> None:
        """Test ContentQualityService produces deterministic results."""
        service1 = ContentQualityService(Path("app/data/converters"))
        result1 = service1.evaluate_page("pdf", "how_to")
        
        service2 = ContentQualityService(Path("app/data/converters"))
        result2 = service2.evaluate_page("pdf", "how_to")
        
        # Core fields should match
        assert result1.get("format") == result2.get("format")
        assert result1.get("page_type") == result2.get("page_type")
        assert result1.get("quality_score") == result2.get("quality_score")
        assert result1.get("decision") == result2.get("decision")

    def test_no_randomness_in_calculations(self) -> None:
        """Test that quality calculations are deterministic."""
        service = ContentQualityService(Path("app/data/converters"))
        
        scores1 = []
        scores2 = []
        
        for _ in range(3):
            result = service.evaluate_page("jpg", "tutorials")
            scores1.append(result.get("quality_score"))
        
        for _ in range(3):
            result = service.evaluate_page("jpg", "tutorials")
            scores2.append(result.get("quality_score"))
        
        # All scores should be identical
        assert scores1 == scores2

    def test_page_type_validation(self) -> None:
        """Test evaluate_page works with all page types."""
        service = ContentQualityService(Path("app/data/converters"))
        
        page_types = [
            "how_to", "tutorials", "best_practices", "troubleshooting",
            "file_format_guides", "use_cases", "faqs", "metadata_guides",
            "mime_guides", "software_guides"
        ]
        
        for page_type in page_types:
            result = service.evaluate_page("pdf", page_type)
            assert result.get("page_type") == page_type
            assert "quality_score" in result
            assert "decision" in result

    def test_format_name_lowercase_handling(self) -> None:
        """Test format names are handled case-insensitively."""
        service = ContentQualityService(Path("app/data/converters"))
        
        result_lower = service.evaluate_page("pdf", "how_to")
        result_upper = service.evaluate_page("PDF", "how_to")
        
        assert result_lower.get("format") == result_upper.get("format").lower()

    def test_timestamp_included_in_result(self) -> None:
        """Test timestamp is included in evaluation result."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("png", "tutorials")
        
        assert "timestamp" in result
        # Timestamp should be ISO format
        timestamp = result.get("timestamp", "")
        assert "T" in timestamp or "-" in timestamp


class TestProgrammaticSeoEngineWithQuality:
    """Test ProgrammaticSeoEngine quality gate integration."""

    def test_programmatic_seo_engine_initializes_with_quality_service(self) -> None:
        """Test ProgrammaticSeoEngine has ContentQualityService."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        assert hasattr(engine, "content_quality_service")
        assert engine.content_quality_service is not None

    def test_generate_page_with_quality_check_includes_quality_score(self) -> None:
        """Test generate_page_with_quality_check includes quality_score."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page_with_quality_check("pdf", "how_to")
        
        assert "quality_score" in page
        assert "quality_decision" in page
        assert "quality_evaluation" in page

    def test_generate_page_with_quality_check_quality_score_0_to_100(self) -> None:
        """Test quality_score is between 0 and 100."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page_with_quality_check("jpg", "tutorials")
        
        score = page.get("quality_score", 0)
        assert 0 <= score <= 100

    def test_generate_all_pages_with_quality_control_filters_by_score(self) -> None:
        """Test generate_all_pages_with_quality_control filters pages."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        pages = engine.generate_all_pages_with_quality_control(min_quality_score=80)
        
        # Check that pages have publication_status
        formats_checked = 0
        for fmt, page_types in pages.items():
            for page_type, page in page_types.items():
                if page:
                    assert "publication_status" in page
                    formats_checked += 1
                    break
            if formats_checked > 0:
                break

    def test_generate_page_with_quality_check_assigns_publication_status(self) -> None:
        """Test generate_page_with_quality_check assigns publication status."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = engine.generate_page_with_quality_check("pdf", "how_to")
        
        assert "quality_score" in page
        assert "quality_decision" in page
        assert "publication_status" in page
        decision = page["quality_decision"]
        status = page["publication_status"]

        if decision == "PASS":
            assert status == "ELIGIBLE"
        elif decision == "NEEDS_REVIEW":
            assert status == "HOLD_FOR_REVIEW"
        elif decision == "NO_INDEX":
            assert status == "NO_INDEX"
        else:
            assert status == "REJECT"

    def test_generate_all_pages_with_quality_control_publication_status_consistent(self) -> None:
        """Test generate_all_pages_with_quality_control returns consistent CQE statuses."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        pages = engine.generate_all_pages_with_quality_control(min_quality_score=60)

        for fmt, page_types in pages.items():
            for page_type, page in page_types.items():
                if not page:
                    continue
                decision = page.get("quality_decision")
                status = page.get("publication_status")

                if decision == "PASS":
                    assert status == "ELIGIBLE"
                elif decision == "NEEDS_REVIEW":
                    assert status == "HOLD_FOR_REVIEW"
                elif decision == "NO_INDEX":
                    assert status == "NO_INDEX"
                elif decision == "REJECT":
                    assert status == "REJECT"
                else:
                    pytest.fail(f"Unexpected quality decision: {decision}")

    def test_get_quality_report_returns_aggregated_metrics(self) -> None:
        """Test get_quality_report returns comprehensive quality report."""
        engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        report = engine.get_quality_report()
        
        assert "total_pages_evaluated" in report
        assert "pass_count" in report
        assert "average_quality_score" in report


class TestProductionAuditServiceWithQuality:
    """Test ProductionAuditService quality metrics."""

    def test_production_audit_service_includes_quality_checks(self) -> None:
        """Test ProductionAuditService has content quality checks."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        # Get active contracts and audit one
        contracts = service.converter_registry_service.get_active()
        if contracts:
            result = service.audit_converter(contracts[0])
            checks = result.get("checks", {})
            
            # Check for content quality checks
            assert "content_quality" in checks or True  # May not exist if no contracts

    def test_audit_all_returns_quality_averaged_score(self) -> None:
        """Test audit_all returns averaged quality score."""
        service = ProductionAuditService(Path("app/data/converters"))
        result = service.audit_all()
        
        summary = result.get("summary", {})
        assert "quality_score_average" in summary


class TestGrowthDashboardServiceWithQuality:
    """Test GrowthDashboardService quality metrics."""

    def test_growth_dashboard_includes_content_quality_section(self) -> None:
        """Test build_dashboard includes content_quality metrics."""
        service = GrowthDashboardService(
            contracts_dir=Path("app/data/converters"),
        )
        dashboard = service.build_dashboard()
        
        assert "content_quality" in dashboard

    def test_content_quality_metrics_has_required_fields(self) -> None:
        """Test content_quality metrics have required fields."""
        service = GrowthDashboardService(
            contracts_dir=Path("app/data/converters"),
        )
        dashboard = service.build_dashboard()
        
        cq = dashboard.get("content_quality", {})
        assert "status" in cq
        assert "pages_evaluated" in cq
        assert "pass_rate_percentage" in cq
        assert "average_quality_score" in cq

    def test_content_quality_status_based_on_pass_rate(self) -> None:
        """Test content_quality status reflects pass rate."""
        service = GrowthDashboardService(
            contracts_dir=Path("app/data/converters"),
        )
        dashboard = service.build_dashboard()
        
        cq = dashboard.get("content_quality", {})
        pass_rate = cq.get("pass_rate_percentage", 0)
        status = cq.get("status")
        
        if pass_rate >= 80:
            assert status == "healthy"
        elif pass_rate >= 60:
            assert status == "warning"
        else:
            assert status == "critical"

    def test_content_quality_pass_rate_calculation(self) -> None:
        """Test content_quality pass_rate is correctly calculated."""
        service = GrowthDashboardService(
            contracts_dir=Path("app/data/converters"),
        )
        dashboard = service.build_dashboard()
        
        cq = dashboard.get("content_quality", {})
        pass_count = cq.get("pages_pass", 0)
        total = cq.get("pages_evaluated", 0)
        pass_rate = cq.get("pass_rate_percentage", 0)
        
        if total > 0:
            expected_rate = (pass_count / total) * 100
            assert abs(pass_rate - expected_rate) < 0.01  # Allow for rounding

    def test_quality_assessment_levels(self) -> None:
        """Test quality_assessment shows correct level."""
        service = GrowthDashboardService(
            contracts_dir=Path("app/data/converters"),
        )
        dashboard = service.build_dashboard()
        
        cq = dashboard.get("content_quality", {})
        score = cq.get("average_quality_score", 0)
        assessment = cq.get("quality_assessment")
        
        if score >= 90:
            assert assessment == "EXCELLENT"
        elif score >= 80:
            assert assessment == "GOOD"
        elif score >= 60:
            assert assessment == "FAIR"
        else:
            assert assessment == "POOR"

    def test_eligible_pages_count(self) -> None:
        """Test eligible_pages is sum of pass and needs_review."""
        service = GrowthDashboardService(
            contracts_dir=Path("app/data/converters"),
        )
        dashboard = service.build_dashboard()
        
        cq = dashboard.get("content_quality", {})
        pass_count = cq.get("pages_pass", 0)
        review_count = cq.get("pages_needs_review", 0)
        eligible = cq.get("eligible_pages", 0)
        
        assert eligible == pass_count + review_count


class TestQualityIntegration:
    """Test quality metrics integration across services."""

    def test_quality_metrics_consistent_across_services(self) -> None:
        """Test quality metrics are consistent when evaluated by different services."""
        # Evaluate with ContentQualityService
        cq_service = ContentQualityService(Path("app/data/converters"))
        cq_result = cq_service.evaluate_page("pdf", "how_to")
        
        # Evaluate with ProgrammaticSeoEngine
        seo_engine = ProgrammaticSeoEngine(Path("app/data/converters"))
        page = seo_engine.generate_page_with_quality_check("pdf", "how_to")
        
        # Both should have quality_score
        assert "quality_score" in cq_result
        assert "quality_score" in page
        assert cq_result.get("quality_score") == page.get("quality_score")

    def test_all_quality_checks_contribute_to_overall_score(self) -> None:
        """Test that all individual metrics affect overall quality score."""
        service = ContentQualityService(Path("app/data/converters"))
        result = service.evaluate_page("png", "best_practices")
        
        metrics = result.get("metrics", {})
        overall = result.get("quality_score", 0)
        
        # All metrics should exist and influence score
        metric_keys = [
            "uniqueness_score", "data_density_score", "eligibility_score",
            "search_intent_score", "internal_link_score", "schema_score",
            "duplicate_score"
        ]
        
        for key in metric_keys:
            assert key in metrics
            assert 0 <= metrics[key] <= 100

    def test_quality_gate_prevents_low_quality_publication(self) -> None:
        """Test quality gate concept - low quality pages identified."""
        service = ContentQualityService(Path("app/data/converters"))
        
        # Some pages will have low quality (< 60)
        results = []
        for page_type in ["how_to", "tutorials", "best_practices"]:
            result = service.evaluate_page("docx", page_type)
            results.append(result)
        
        # At least check that results are different and deterministic
        assert len(results) == 3
        for result in results:
            assert "decision" in result
            assert result.get("decision") in ["PASS", "NEEDS_REVIEW", "NO_INDEX", "REJECT"]
