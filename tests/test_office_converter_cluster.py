import pytest
from pathlib import Path

from app.services.converter_registry_service import ConverterRegistryService
from app.services.converter_data_service import ConverterDataService
from app.services.landing_service import LandingPageBuilder
from app.services.knowledge_service import KnowledgeService
from app.services.related_converter_service import RelatedConverterService
from app.services.hub_page_service import HubPageService
from app.services.sitemap_service import SitemapService
from app.services.production_audit_service import ProductionAuditService
from app.services.seo_service import SeoService


SLUGS = [
    "docx-to-pdf",
    "pdf-to-docx",
    "xlsx-to-pdf",
    "pdf-to-xlsx",
    "pptx-to-pdf",
    "pdf-to-pptx",
    "odt-to-pdf",
    "pdf-to-odt",
    "ods-to-xlsx",
    "xlsx-to-ods",
]


def test_contracts_loadable():
    svc = ConverterRegistryService("app/data/converters")
    active = [c.get("slug") for c in svc.get_active()]
    for slug in SLUGS:
        assert slug in active


def test_converter_data_and_landing_build():
    data_svc = ConverterDataService(Path("app/data/converters"))
    seo = SeoService(Path("app/data/converters"))
    builder = LandingPageBuilder(seo, data_svc)
    for slug in SLUGS:
        data = data_svc.load_converter_by_slug(slug)
        ctx = builder.build_context(type("Request", (), {})(), data)
        builder.validate_contract(ctx)
        assert ctx.get("h1") and ctx.get("steps")


def test_knowledge_and_related():
    data_svc = ConverterDataService(Path("app/data/converters"))
    knowledge = KnowledgeService(Path("app/data/converters"))
    related = RelatedConverterService(data_svc)
    for slug in SLUGS:
        contract = data_svc.load_converter_by_slug(slug)
        payload = knowledge.generate_payload(contract)
        assert payload
        rel = related.get_related_converters(contract, limit=3)
        assert isinstance(rel, list)


def test_hub_and_sitemap_and_audit():
    registry_svc = ConverterRegistryService(Path("app/data/converters"))
    # ensure registry can enumerate active converters
    active = registry_svc.get_active()
    # register active contracts into the global registry via ProductionAuditService
    from app.services.production_audit_service import ProductionAuditService
    ProductionAuditService(contracts_dir=Path("app/data/converters"))

    sitemap = SitemapService(output_dir=Path("outputs/sitemaps"))
    sitemap.generate_all(base_url="https://converigo.com")
    assert sitemap.validate() == []

    hub = HubPageService()
    pages = hub.build_all()
    # ensure each slug appears in at least one hub page
    for slug in SLUGS:
        found = any(any(c.get("id") == slug for c in p.get("converter_list", [])) for p in pages.values())
        assert found, f"{slug} not found in hub pages"

    pa = ProductionAuditService(contracts_dir=Path("app/data/converters"))
    # audit each office converter individually and ensure READY
    registry_svc = ConverterRegistryService(Path("app/data/converters"))
    for slug in SLUGS:
        contract = registry_svc.get_by_slug(slug)
        assert contract is not None
        result = pa.audit_converter(contract)
        assert result["quality_score"] >= 90, f"{slug} score {result['quality_score']}"
        assert result["status"] == "READY", f"{slug} status {result['status']}"
