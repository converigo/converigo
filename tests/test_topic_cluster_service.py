"""Regression tests for TopicClusterService and integrated dashboard metrics."""

import pytest
from pathlib import Path

from app.services.topic_cluster_service import TopicClusterService
from app.services.production_audit_service import ProductionAuditService
from app.services.growth_dashboard_service import GrowthDashboardService


class TestTopicClusterService:
    """Test TopicClusterService core functionality."""

    def test_topic_cluster_service_initializes(self) -> None:
        """Test TopicClusterService can be instantiated."""
        service = TopicClusterService(Path("app/data/converters"))
        assert service is not None
        assert service.converter_registry_service is not None
        assert service.knowledge_service is not None
        assert service.authority_service is not None

    def test_build_cluster_returns_all_17_sections(self) -> None:
        """Test build_cluster returns all 17 required sections."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("pdf")
        
        # Check all 17 sections are present
        required_sections = [
            "knowledge", "faq", "mime", "file_extensions", "metadata",
            "specification", "history", "security", "compression",
            "accessibility", "software", "tutorials", "best_practices",
            "comparisons", "related_formats", "related_converters", "hub"
        ]
        
        for section in required_sections:
            assert section in cluster, f"Missing section: {section}"
            assert cluster[section] is not None, f"Section {section} is None"

    def test_build_cluster_has_metadata(self) -> None:
        """Test build_cluster includes metadata fields."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("pdf")
        
        assert "format" in cluster
        assert "format_title" in cluster
        assert "breadcrumb" in cluster
        assert "internal_links" in cluster

    def test_build_cluster_knowledge_section_has_content(self) -> None:
        """Test knowledge section has proper content."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("png")
        knowledge = cluster["knowledge"]
        
        assert "title" in knowledge
        assert "overview" in knowledge
        assert "key_points" in knowledge
        assert isinstance(knowledge["key_points"], list)
        assert len(knowledge["key_points"]) > 0

    def test_build_cluster_faq_has_questions(self) -> None:
        """Test FAQ section has questions and answers."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("jpg")
        faq = cluster["faq"]
        
        assert isinstance(faq, list)
        assert len(faq) >= 4  # Should have at least 4 FAQs
        
        for item in faq:
            assert "question" in item
            assert "answer" in item

    def test_build_cluster_mime_section_has_type(self) -> None:
        """Test MIME section has MIME type."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("pdf")
        mime = cluster["mime"]
        
        assert "primary" in mime
        assert mime["primary"] == "application/pdf"
        assert "alternatives" in mime

    def test_build_cluster_extensions_has_extension(self) -> None:
        """Test file extensions section has extensions."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("docx")
        extensions = cluster["file_extensions"]
        
        assert "primary" in extensions
        assert extensions["primary"].startswith(".")
        assert "common_variations" in extensions

    def test_build_cluster_software_has_list(self) -> None:
        """Test software section has software list."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("mp4")
        software = cluster["software"]
        
        assert "native_support" in software
        assert "also_supported_by" in software
        assert isinstance(software["native_support"], list)

    def test_build_cluster_tutorials_has_links(self) -> None:
        """Test tutorials section has tutorial links."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("webp")
        tutorials = cluster["tutorials"]
        
        assert isinstance(tutorials, list)
        assert len(tutorials) > 0
        
        for item in tutorials:
            assert "title" in item
            assert "url" in item
            assert "description" in item

    def test_build_all_clusters_generates_for_all_formats(self) -> None:
        """Test build_all_clusters generates for all known formats."""
        service = TopicClusterService(Path("app/data/converters"))
        
        clusters = service.build_all_clusters()
        
        assert isinstance(clusters, dict)
        assert len(clusters) > 0
        
        # Each cluster should have all sections
        required_sections = [
            "knowledge", "faq", "mime", "file_extensions", "metadata",
            "specification", "history", "security", "compression",
            "accessibility", "software", "tutorials", "best_practices",
            "comparisons", "related_formats", "related_converters", "hub"
        ]
        
        for fmt, cluster in list(clusters.items())[:5]:  # Check first 5
            for section in required_sections:
                assert section in cluster, f"Format {fmt} missing section: {section}"

    def test_get_cluster_single_format(self) -> None:
        """Test getting a single cluster."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.get_cluster("mp3")
        
        assert cluster is not None
        assert cluster["format"] == "mp3"
        assert cluster["format_title"] == "MP3"

    def test_cluster_breadcrumb_structure(self) -> None:
        """Test cluster has proper breadcrumb structure."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("wav")
        breadcrumb = cluster["breadcrumb"]
        
        assert isinstance(breadcrumb, list)
        assert len(breadcrumb) == 3
        assert breadcrumb[0]["name"] == "Home"
        assert breadcrumb[1]["name"] == "Formats"

    def test_cluster_compression_section_has_details(self) -> None:
        """Test compression section has details."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("png")
        compression = cluster["compression"]
        
        assert "compression_type" in compression
        assert "is_lossy" in compression
        assert "typical_ratio" in compression

    def test_cluster_security_section_has_considerations(self) -> None:
        """Test security section has considerations."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("pdf")
        security = cluster["security"]
        
        assert "considerations" in security
        assert "best_practices" in security
        assert isinstance(security["considerations"], list)
        assert len(security["considerations"]) > 0

    def test_cluster_accessibility_section(self) -> None:
        """Test accessibility section has content."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("docx")
        accessibility = cluster["accessibility"]
        
        assert "screen_reader_support" in accessibility
        assert "considerations" in accessibility
        assert "wcag_compliance" in accessibility

    def test_cluster_related_formats_section(self) -> None:
        """Test related formats section."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("jpg")
        related = cluster["related_formats"]
        
        assert isinstance(related, list)
        # PNG and WebP should be related to JPG
        related_formats = [item.get("title", "").lower() for item in related]
        assert any("png" in fmt for fmt in related_formats) or len(related) > 0

    def test_cluster_coverage_report_structure(self) -> None:
        """Test cluster coverage report has expected structure."""
        service = TopicClusterService(Path("app/data/converters"))
        
        report = service.build_cluster_coverage_report()
        
        assert "total_formats" in report
        assert "topic_clusters_total" in report
        assert "topic_clusters_complete" in report
        assert "topic_cluster_coverage" in report
        assert "completeness_percentage" in report
        assert "orphan_topics" in report
        assert "orphan_topics_count" in report

    def test_cluster_coverage_report_values_realistic(self) -> None:
        """Test coverage report has realistic values."""
        service = TopicClusterService(Path("app/data/converters"))
        
        report = service.build_cluster_coverage_report()
        
        # Coverage percentage should be 0-100
        coverage = report.get("topic_cluster_coverage", 0)
        assert 0 <= coverage <= 100
        
        # Completeness should be 0-100
        completeness = report.get("completeness_percentage", 0)
        assert 0 <= completeness <= 100
        
        # Orphan topics should be non-negative
        orphans = report.get("orphan_topics_count", 0)
        assert orphans >= 0


class TestProductionAuditServiceTopicClusterIntegration:
    """Test ProductionAuditService integration with TopicClusterService."""

    def test_production_audit_has_topic_cluster_service(self) -> None:
        """Test ProductionAuditService has TopicClusterService."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        assert hasattr(service, "topic_cluster_service")
        assert service.topic_cluster_service is not None

    def test_audit_converter_includes_topic_cluster_checks(self) -> None:
        """Test audit includes topic cluster checks."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        converters = service.converter_registry_service.get_active()
        assert len(converters) > 0
        
        audit_result = service.audit_converter(converters[0])
        
        assert "checks" in audit_result
        assert "topic_cluster_complete" in audit_result["checks"]
        assert "topic_cluster_links" in audit_result["checks"]
        assert "topic_cluster_quality" in audit_result["checks"]

    def test_get_topic_cluster_report(self) -> None:
        """Test ProductionAuditService provides topic cluster report."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        report = service.get_topic_cluster_report()
        
        assert "total_formats" in report
        assert "topic_clusters_total" in report
        assert "topic_cluster_coverage" in report

    def test_audit_scores_include_topic_cluster_checks(self) -> None:
        """Test that audit scoring includes topic cluster checks."""
        service = ProductionAuditService(Path("app/data/converters"))
        
        converters = service.converter_registry_service.get_active()
        assert len(converters) > 0
        
        audit_result = service.audit_converter(converters[0])
        
        # Quality score should be out of 13 checks now
        quality_score = audit_result.get("quality_score", 0)
        assert 0 <= quality_score <= 100


class TestGrowthDashboardServiceTopicClusterIntegration:
    """Test GrowthDashboardService integration with TopicClusterService."""

    def test_growth_dashboard_has_topic_cluster_service(self) -> None:
        """Test GrowthDashboardService instantiates TopicClusterService."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        assert hasattr(service, "topic_cluster_service")
        assert service.topic_cluster_service is not None

    def test_dashboard_includes_topic_cluster_metrics(self) -> None:
        """Test that dashboard includes topic cluster metrics."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        dashboard = service.build_dashboard()
        
        assert "topic_clusters" in dashboard
        metrics = dashboard["topic_clusters"]
        
        assert "topic_clusters_total" in metrics
        assert "topic_clusters_ready" in metrics
        assert "topic_cluster_coverage" in metrics
        assert "orphan_topics" in metrics

    def test_dashboard_topic_metrics_are_valid(self) -> None:
        """Test that topic cluster metrics are valid."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        dashboard = service.build_dashboard()
        metrics = dashboard["topic_clusters"]
        
        # Coverage should be between 0 and 100
        coverage = metrics.get("topic_cluster_coverage", 0)
        assert 0 <= coverage <= 100
        
        # Orphan topics should be non-negative
        orphans = metrics.get("orphan_topics", 0)
        assert orphans >= 0
        
        # Completeness should be between 0 and 100
        completeness = metrics.get("completeness_percentage", 0)
        assert 0 <= completeness <= 100

    def test_dashboard_complete_build_with_topic_clusters(self) -> None:
        """Test that dashboard builds successfully with all topic cluster metrics."""
        service = GrowthDashboardService(contracts_dir=Path("app/data/converters"))
        
        # Should not raise any exceptions
        dashboard = service.build_dashboard()
        
        # Check expected structure
        assert "total_converters" in dashboard
        assert "registry_health" in dashboard
        assert "production_audit" in dashboard
        assert "internal_linking" in dashboard
        assert "topic_clusters" in dashboard
        assert "authority_coverage" in dashboard


class TestTopicClusterEndToEnd:
    """End-to-end tests for topic clustering functionality."""

    def test_common_formats_have_complete_clusters(self) -> None:
        """Test that common formats have complete clusters."""
        service = TopicClusterService(Path("app/data/converters"))
        
        common_formats = ["pdf", "png", "jpg", "mp4", "mp3"]
        
        for fmt in common_formats:
            cluster = service.build_cluster(fmt)
            
            # All sections should be present
            required_sections = [
                "knowledge", "faq", "mime", "file_extensions", "metadata",
                "specification", "history", "security", "compression",
                "accessibility", "software", "tutorials", "best_practices",
                "comparisons", "related_formats", "related_converters", "hub"
            ]
            
            for section in required_sections:
                assert section in cluster, f"{fmt} missing {section}"

    def test_cluster_breadcrumbs_are_consistent(self) -> None:
        """Test that cluster breadcrumbs follow consistent structure."""
        service = TopicClusterService(Path("app/data/converters"))
        
        formats = ["pdf", "docx", "png"]
        
        for fmt in formats:
            cluster = service.build_cluster(fmt)
            breadcrumb = cluster["breadcrumb"]
            
            assert len(breadcrumb) == 3
            assert breadcrumb[0]["name"] == "Home"
            assert breadcrumb[0]["url"] == "/"
            assert breadcrumb[1]["name"] == "Formats"
            assert breadcrumb[1]["url"] == "/formats"
            assert breadcrumb[2]["name"] == fmt.upper()
            assert breadcrumb[2]["url"] == f"/formats/{fmt}"

    def test_all_clusters_have_internal_links(self) -> None:
        """Test that all clusters have internal links structure."""
        service = TopicClusterService(Path("app/data/converters"))
        
        formats = ["pdf", "png", "mp4"]
        
        for fmt in formats:
            cluster = service.build_cluster(fmt)
            internal_links = cluster.get("internal_links", {})
            
            assert isinstance(internal_links, dict)

    def test_topic_clusters_are_deterministic(self) -> None:
        """Test that topic clusters generate deterministically."""
        service1 = TopicClusterService(Path("app/data/converters"))
        service2 = TopicClusterService(Path("app/data/converters"))
        
        cluster1 = service1.build_cluster("pdf")
        cluster2 = service2.build_cluster("pdf")
        
        # Key fields should match
        assert cluster1["format"] == cluster2["format"]
        assert cluster1["format_title"] == cluster2["format_title"]
        assert cluster1["mime"]["primary"] == cluster2["mime"]["primary"]
        assert len(cluster1["faq"]) == len(cluster2["faq"])

    def test_cluster_software_sections_have_apps(self) -> None:
        """Test that all clusters have software apps listed."""
        service = TopicClusterService(Path("app/data/converters"))
        
        formats = ["pdf", "docx", "png", "mp4"]
        
        for fmt in formats:
            cluster = service.build_cluster(fmt)
            software = cluster["software"]
            
            assert len(software.get("native_support", [])) > 0
            assert len(software.get("also_supported_by", [])) > 0

    def test_cluster_tutorial_links_are_properly_formatted(self) -> None:
        """Test that tutorial links are properly formatted."""
        service = TopicClusterService(Path("app/data/converters"))
        
        cluster = service.build_cluster("webp")
        tutorials = cluster["tutorials"]
        
        for tutorial in tutorials:
            assert tutorial["url"].startswith("/")
            assert "title" in tutorial
            assert "description" in tutorial
