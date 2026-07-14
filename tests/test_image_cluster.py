from pathlib import Path

from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.landing_service import LandingPageBuilder
from app.services.related_converter_service import RelatedConverterService
from app.services.seo_service import SeoService


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"
NEW_SLUGS = ["jpg-to-png", "png-to-jpg", "png-to-webp", "webp-to-png", "avif-to-jpg"]


class DummyRequest:
    pass


def _build_builder() -> LandingPageBuilder:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    seo_service = SeoService(CONVERTERS_DIR)
    return LandingPageBuilder(seo_service, converter_data_service)


def test_registry_discovers_image_cluster_converters() -> None:
    registry = ConverterRegistryService(CONVERTERS_DIR)
    discovered_slugs = {contract["slug"] for contract in registry.list_all()}

    for slug in NEW_SLUGS:
        assert slug in discovered_slugs


def test_landing_contract_passes_for_image_cluster_converters() -> None:
    builder = _build_builder()
    converter_data_service = ConverterDataService(CONVERTERS_DIR)

    for slug in NEW_SLUGS:
        tool_data = converter_data_service.load_converter_by_slug(slug)
        landing = builder.build_context(DummyRequest(), tool_data)
        assert landing["h1"]
        assert landing["seo_title"]
        assert landing["meta_description"]
        assert landing["intro"]["title"]
        assert landing["intro"]["text"]
        assert landing["faq"]
        assert landing["json_ld"]
        assert landing["breadcrumb"]
        assert landing["cta"]
        assert landing["download"]
        assert landing["related_converter"]
        assert landing["internal_links"]


def test_related_converter_service_supports_image_cluster() -> None:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    service = RelatedConverterService(converter_data_service)

    converter = converter_data_service.load_converter_by_slug("png-to-webp")
    related = service.get_related_converters(converter, limit=4)

    assert len(related) >= 4
    assert converter["slug"] not in {item["slug"] for item in related}
    assert len({item["slug"] for item in related}) == len(related)
