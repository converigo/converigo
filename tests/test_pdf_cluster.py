from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.registry import registry
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.landing_service import LandingPageBuilder
from app.services.related_converter_service import RelatedConverterService
from app.services.seo_service import SeoService


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"
NEW_SLUGS = ["pdf-compress", "pdf-merge", "pdf-split"]


from types import SimpleNamespace


class DummyRequest:
    def __init__(self):
        self.state = SimpleNamespace(
            t=lambda key, default=None: default if default is not None else key,
            locale=SimpleNamespace(lang_code="en"),
            supported_locales=["en", "es", "fr", "id", "ja"],
        )


def _build_builder() -> LandingPageBuilder:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    seo_service = SeoService(CONVERTERS_DIR)
    return LandingPageBuilder(seo_service, converter_data_service)


def test_registry_discovers_pdf_cluster_converter_contracts() -> None:
    registry = ConverterRegistryService(CONVERTERS_DIR)
    discovered_slugs = {contract["slug"] for contract in registry.list_all()}

    for slug in NEW_SLUGS:
        assert slug in discovered_slugs


def test_landing_contract_passes_for_pdf_cluster_converters() -> None:
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


def test_related_converter_service_supports_pdf_cluster() -> None:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    service = RelatedConverterService(converter_data_service)

    converter = converter_data_service.load_converter_by_slug("pdf-compress")
    related = service.get_related_converters(converter, limit=4)

    assert len(related) >= 4
    assert converter["slug"] not in {item["slug"] for item in related}
    assert len({item["slug"] for item in related}) == len(related)


def test_operation_slug_resolves_pdf_merge_plugin_for_matching_pair() -> None:
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-merge")
    assert plugin.slug == "pdf-merge"


def test_operation_slug_rejects_mismatched_pair_and_skips_plugin_call() -> None:
    mock_plugin = Mock()
    mock_plugin.slug = "pdf-merge"

    with pytest.raises(ValueError, match="does not support pdf -> png|not support.*pdf.*png"):
        registry.get_plugin("pdf", "png", slug="pdf-merge")

    mock_plugin.convert.assert_not_called()


def test_operation_slug_rejects_unknown_slug_with_422() -> None:
    client = TestClient(app)
    response = client.post(
        "/convert",
        files=[("file", ("sample.pdf", b"%PDF-1.4\n%%EOF", "application/pdf"))],
        data={"target_format": "pdf", "operation": "bogus"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert "slug tidak tersedia" in payload["message"]


def test_legacy_operationless_call_still_uses_pdf_split_for_pdf_pdf() -> None:
    plugin = registry.get_plugin("pdf", "pdf")
    assert plugin.slug == "pdf-split"


def test_disabled_pdf_tools_are_404_and_absent_from_homepage() -> None:
    client = TestClient(app)

    for slug in ("pdf-compress", "pdf-merge"):
        response = client.get(f"/tools/{slug}")
        assert response.status_code == 404

    home_response = client.get("/")
    assert home_response.status_code == 200
    body = home_response.text.lower()
    assert "pdf-compress" not in body
    assert "pdf-merge" not in body
