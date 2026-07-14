"""
Test Archive Converter Cluster

Verify all 5 archive converters are properly registered, contracted, 
and ready for production.
"""

import json
from pathlib import Path

import pytest

from app.services.converter_registry_service import ConverterRegistryService
from app.services.converter_data_service import ConverterDataService
from app.services.production_audit_service import ProductionAuditService
from app.services.related_converter_service import RelatedConverterService
from app.plugins import discover_plugin_classes


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def contracts_dir():
    """Path to converter contracts directory."""
    return Path("app/data/converters")


@pytest.fixture
def registry_service(contracts_dir):
    """ConverterRegistryService instance."""
    return ConverterRegistryService(contracts_dir)


@pytest.fixture
def data_service(contracts_dir):
    """ConverterDataService instance."""
    return ConverterDataService(contracts_dir)


@pytest.fixture
def audit_service(contracts_dir):
    """ProductionAuditService instance."""
    return ProductionAuditService(contracts_dir)


@pytest.fixture
def related_service(data_service):
    """RelatedConverterService instance."""
    return RelatedConverterService(data_service)


# ==========================================
# Tests: Contract Validation
# ==========================================

class TestArchiveConverterContracts:
    """Test archive converter contracts are valid."""
    
    ARCHIVE_SLUGS = {
        "zip-extract",
        "rar-extract", 
        "7z-extract",
        "tar-extract",
        "gz-extract"
    }
    
    def test_all_archive_contracts_exist(self, registry_service):
        """Verify all 5 archive converters have valid contracts."""
        all_contracts = registry_service.list_all()
        contract_slugs = {c["slug"] for c in all_contracts}
        
        for slug in self.ARCHIVE_SLUGS:
            assert slug in contract_slugs, f"Missing contract for {slug}"
    
    def test_archive_contracts_have_valid_schema(self, registry_service):
        """Verify archive contracts match required schema."""
        all_contracts = registry_service.list_all()
        archive_contracts = [c for c in all_contracts if c["slug"] in self.ARCHIVE_SLUGS]
        
        for contract in archive_contracts:
            assert contract["category"] == "archive"
            assert contract["conversion_engine"] == "archive"
            assert contract["seo_status"] == "ready"
            assert contract["schema_status"] == "ready"
            assert contract["faq_status"] == "ready"
            assert contract["lifecycle_status"] == "active"
    
    def test_archive_contract_fields_valid(self, registry_service):
        """Verify all required fields are present and valid."""
        all_contracts = registry_service.list_all()
        archive_contracts = [c for c in all_contracts if c["slug"] in self.ARCHIVE_SLUGS]
        
        for contract in archive_contracts:
            # ID and slug match
            assert contract["id"] == contract["slug"]
            
            # Has name
            assert contract["name"]
            assert len(contract["name"]) > 0
            
            # Has description
            assert contract["description"]
            assert len(contract["description"]) > 0
            
            # Input/output formats
            assert len(contract["input_formats"]) > 0
            assert len(contract["output_formats"]) > 0
            
            # MIME types
            assert len(contract["accepted_mime_types"]) > 0
            
            # Max upload size (500MB)
            assert contract["max_upload_size"] > 0
            assert contract["max_upload_size"] >= 104857600  # At least 100MB
            
            # URLs
            assert contract["landing_path"].startswith("/")
            assert contract["canonical_url"].startswith("https://")
            
            # Sample for testing
            assert contract["regression_sample"]
    
    def test_archive_converters_unique(self, registry_service):
        """Verify no duplicate IDs or slugs."""
        all_contracts = registry_service.list_all()
        archive_contracts = [c for c in all_contracts if c["slug"] in self.ARCHIVE_SLUGS]
        
        ids = [c["id"] for c in archive_contracts]
        slugs = [c["slug"] for c in archive_contracts]
        
        assert len(ids) == len(set(ids)), "Duplicate converter IDs found"
        assert len(slugs) == len(set(slugs)), "Duplicate converter slugs found"


# ==========================================
# Tests: Plugin Discovery
# ==========================================

class TestArchivePlugins:
    """Test archive plugins are discovered and instantiated."""
    
    ARCHIVE_SLUGS = {
        "zip-extract",
        "rar-extract",
        "7z-extract", 
        "tar-extract",
        "gz-extract"
    }
    
    def test_archive_plugins_discovered(self):
        """Verify all 5 archive plugins are discovered."""
        plugin_classes = discover_plugin_classes()
        plugin_slugs = {p().slug for p in plugin_classes}
        
        for slug in self.ARCHIVE_SLUGS:
            assert slug in plugin_slugs, f"Plugin not discovered for {slug}"
    
    def test_archive_plugins_have_valid_metadata(self):
        """Verify plugins have required metadata."""
        plugin_classes = discover_plugin_classes()
        archive_plugins = [p() for p in plugin_classes if p().slug in self.ARCHIVE_SLUGS]
        
        assert len(archive_plugins) == 5
        
        for plugin in archive_plugins:
            assert plugin.slug
            assert plugin.name
            assert plugin.description
            assert plugin.category == "archive"
            assert plugin.engine == "archive"
            assert plugin.icon
            assert plugin.seo_title
            assert plugin.seo_description
            
            # Quality scoring
            assert 0 <= plugin.priority <= 100
            assert 0 <= plugin.quality <= 100
            assert 0 <= plugin.compatibility <= 100
    
    def test_archive_plugins_support_formats(self):
        """Verify plugins declare supported formats correctly."""
        plugin_classes = discover_plugin_classes()
        archive_plugins = [p() for p in plugin_classes if p().slug in self.ARCHIVE_SLUGS]
        
        format_map = {
            "zip-extract": ("zip", "zip"),
            "rar-extract": ("rar", "rar"),
            "7z-extract": ("7z", "7z"),
            "tar-extract": ("tar", "tar"),
            "gz-extract": ("gz", "gz")
        }
        
        for plugin in archive_plugins:
            expected_source, expected_target = format_map[plugin.slug]
            assert expected_source in [f.lower() for f in plugin.source_formats]
            assert expected_target in [f.lower() for f in plugin.target_formats]


# ==========================================
# Tests: Landing Page Data
# ==========================================

class TestArchiveConverterData:
    """Test landing page data for archive converters."""
    
    ARCHIVE_SLUGS = {
        "zip-extract",
        "rar-extract",
        "7z-extract",
        "tar-extract",
        "gz-extract"
    }
    
    def test_all_archive_data_files_exist(self, data_service):
        """Verify all 5 converters have data files."""
        all_data = data_service.list_all_converters()
        data_slugs = {d["slug"] for d in all_data}
        
        for slug in self.ARCHIVE_SLUGS:
            assert slug in data_slugs, f"Missing data file for {slug}"
    
    def test_archive_data_has_required_sections(self, data_service):
        """Verify archive data files have all required landing sections."""
        all_data = data_service.list_all_converters()
        archive_data = [d for d in all_data if d["slug"] in self.ARCHIVE_SLUGS]
        
        required_sections = [
            "slug",
            "title",
            "description",
            "hero",
            "features",
            "how_to_use",
            "about_formats",
            "faq",
            "related_tools",
            "cta",
            "seo"
        ]
        
        for data in archive_data:
            for section in required_sections:
                assert section in data, f"Missing {section} in {data['slug']}"
    
    def test_archive_data_hero_complete(self, data_service):
        """Verify hero sections are complete."""
        all_data = data_service.list_all_converters()
        archive_data = [d for d in all_data if d["slug"] in self.ARCHIVE_SLUGS]
        
        hero_fields = ["eyebrow", "title", "description", "panel_label", "panel_title"]
        
        for data in archive_data:
            hero = data["hero"]
            for field in hero_fields:
                assert field in hero
                assert hero[field]
    
    def test_archive_data_faq_populated(self, data_service):
        """Verify FAQ sections have content."""
        all_data = data_service.list_all_converters()
        archive_data = [d for d in all_data if d["slug"] in self.ARCHIVE_SLUGS]
        
        for data in archive_data:
            assert len(data["faq"]) >= 6, f"FAQ too short for {data['slug']}"
            for faq_item in data["faq"]:
                assert "question" in faq_item
                assert "answer" in faq_item
                assert faq_item["question"]
                assert faq_item["answer"]
    
    def test_archive_data_related_tools_valid(self, data_service):
        """Verify related tools reference valid converters."""
        all_data = data_service.list_all_converters()
        archive_data = [d for d in all_data if d["slug"] in self.ARCHIVE_SLUGS]
        all_slugs = {d["slug"] for d in all_data}
        
        for data in archive_data:
            for related in data.get("related_tools", []):
                assert related["slug"] in all_slugs
                assert related["title"]


# ==========================================
# Tests: Production Audit
# ==========================================

class TestArchiveProductionAudit:
    """Test production audit scoring for archive converters."""
    
    ARCHIVE_SLUGS = {
        "zip-extract",
        "rar-extract",
        "7z-extract",
        "tar-extract",
        "gz-extract"
    }
    
    def test_archive_converters_pass_production_audit(self, audit_service):
        """Verify all archive converters reach good production quality."""
        audit_results = audit_service.audit_all()
        results_by_slug = {r["slug"]: r for r in audit_results["results"]}
        
        for slug in self.ARCHIVE_SLUGS:
            audit_result = results_by_slug.get(slug)
            assert audit_result, f"No audit result for {slug}"
            
            # Must reach at least WARNING or better status
            # READY (90+), WARNING (70-89), NOT READY (<70)
            assert audit_result["status"] in ["READY", "WARNING"], \
                f"{slug} failed audit: {audit_result.get('checks', {})}"
            
            # Must reach 85+ quality score
            assert audit_result["quality_score"] >= 85, \
                f"{slug} score too low: {audit_result['quality_score']}"
    
    def test_archive_converters_high_quality_score(self, audit_service):
        """Verify archive converters meet quality thresholds."""
        audit_results = audit_service.audit_all()
        results_by_slug = {r["slug"]: r for r in audit_results["results"]}
        scores = {}
        
        for slug in self.ARCHIVE_SLUGS:
            result = results_by_slug.get(slug)
            assert result, f"No audit result for {slug}"
            scores[slug] = result["quality_score"]
            
            # Min 85, target 90+
            assert result["quality_score"] >= 85
            assert result["quality_score"] <= 100
        
        # All should be similar quality
        avg_score = sum(scores.values()) / len(scores)
        for slug, score in scores.items():
            deviation = abs(score - avg_score)
            assert deviation <= 10, f"{slug} quality deviates too much: {score}"


# ==========================================
# Tests: Related Converters Discovery
# ==========================================

class TestArchiveRelatedConverters:
    """Test related converter discovery for archive converters."""
    
    ARCHIVE_SLUGS = {
        "zip-extract",
        "rar-extract",
        "7z-extract",
        "tar-extract",
        "gz-extract"
    }
    
    def test_archive_related_converters_discovered(self, related_service, data_service):
        """Verify related converters are discovered for archive tools."""
        all_data = data_service.list_all_converters()
        
        for slug in self.ARCHIVE_SLUGS:
            converter_data = next((d for d in all_data if d["slug"] == slug), None)
            assert converter_data, f"No data for {slug}"
            
            related = related_service.get_related_converters(converter_data)
            
            # Should find some related converters
            assert len(related) > 0, f"No related converters for {slug}"


# ==========================================
# Tests: Integration
# ==========================================

class TestArchiveClusterIntegration:
    """Integration tests for archive converter cluster."""
    
    def test_archive_cluster_completeness(
        self,
        registry_service,
        data_service,
        audit_service,
        related_service
    ):
        """Verify archive cluster is complete and functional."""
        archive_slugs = {"zip-extract", "rar-extract", "7z-extract", "tar-extract", "gz-extract"}
        
        # All have contracts
        contracts = registry_service.list_all()
        contract_slugs = {c["slug"] for c in contracts if c["slug"] in archive_slugs}
        assert len(contract_slugs) == 5
        
        # All have data
        all_data = data_service.list_all_converters()
        data_slugs = {d["slug"] for d in all_data if d["slug"] in archive_slugs}
        assert len(data_slugs) == 5
        
        # All pass quality checks
        audit_results = audit_service.audit_all()
        results_by_slug = {r["slug"]: r for r in audit_results["results"]}
        for slug in archive_slugs:
            audit = results_by_slug.get(slug)
            assert audit, f"No audit for {slug}"
            assert audit["status"] in ["READY", "WARNING"]
            assert audit["quality_score"] >= 85
        
        # All have related converters
        for slug in archive_slugs:
            converter_data = next((d for d in all_data if d["slug"] == slug), None)
            assert converter_data
            related = related_service.get_related_converters(converter_data)
            assert len(related) > 0
    
    def test_archive_plugins_discoverable(self):
        """Verify plugins are discoverable via auto-discovery."""
        plugin_classes = discover_plugin_classes()
        archive_plugins = [
            p for p in plugin_classes 
            if p().slug in {"zip-extract", "rar-extract", "7z-extract", "tar-extract", "gz-extract"}
        ]
        
        assert len(archive_plugins) == 5
        
        # All have convert method
        for plugin_class in archive_plugins:
            plugin = plugin_class()
            assert hasattr(plugin, "convert")
            assert callable(plugin.convert)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
