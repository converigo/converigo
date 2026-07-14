from pathlib import Path

import pytest

from app.services.converter_data_service import ConverterDataService
from app.services.landing_service import LandingContractError, LandingPageBuilder
from app.services.seo_service import SeoService


class DummyRequest:
    pass


def _build_builder() -> LandingPageBuilder:
    converter_dir = Path(__file__).resolve().parents[1] / "app" / "data" / "converters"
    converter_data_service = ConverterDataService(converter_dir)
    seo_service = SeoService(converter_dir)
    return LandingPageBuilder(seo_service, converter_data_service)


def test_every_active_converter_landing_exposes_the_full_contract() -> None:
    builder = _build_builder()
    converter_data_service = ConverterDataService(Path(__file__).resolve().parents[1] / "app" / "data" / "converters")

    for tool_data in converter_data_service.list_active_converters():
        landing = builder.build_context(DummyRequest(), tool_data)

        assert landing["h1"]
        assert landing["seo_title"]
        assert landing["meta_description"]
        assert landing["intro"]["title"]
        assert landing["intro"]["text"]
        assert landing["steps"]
        assert landing["benefits"]
        assert landing["supported_formats"]
        assert landing["tips"]
        assert landing["common_problems"]
        assert landing["faq"]
        assert 8 <= len(landing["faq"]) <= 12
        assert landing["json_ld"]
        assert landing["breadcrumb"]
        assert landing["cta"]
        assert landing["download"]
        assert landing["related_converter"]
        assert landing["related_converters"]
        assert landing["internal_links"]


def test_landing_contract_validation_fails_when_a_section_is_missing() -> None:
    builder = _build_builder()
    converter_data_service = ConverterDataService(Path(__file__).resolve().parents[1] / "app" / "data" / "converters")
    tool_data = converter_data_service.load_converter_by_slug("mp4-to-mp3")

    landing = builder.build_context(DummyRequest(), tool_data)
    landing.pop("download")

    with pytest.raises(LandingContractError):
        builder.validate_contract(landing)
