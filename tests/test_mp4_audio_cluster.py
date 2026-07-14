from pathlib import Path

from app.services.converter_data_service import ConverterDataService
from app.services.landing_service import LandingPageBuilder
from app.services.converter_registry_service import ConverterRegistryService
from app.services.seo_service import SeoService


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"
NEW_SLUGS = ["mp4-to-wav", "mp4-to-aac", "mp4-to-flac", "mp4-to-ogg", "mp4-to-m4a"]


class DummyRequest:
    pass


def _build_builder() -> LandingPageBuilder:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    seo_service = SeoService(CONVERTERS_DIR)
    return LandingPageBuilder(seo_service, converter_data_service)


def test_registry_discovers_mp4_audio_converter_contracts() -> None:
    registry = ConverterRegistryService(CONVERTERS_DIR)
    discovered_slugs = {contract["slug"] for contract in registry.list_all()}

    for slug in NEW_SLUGS:
        assert slug in discovered_slugs


def test_landing_contract_passes_for_mp4_audio_converters() -> None:
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
