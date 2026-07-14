from pathlib import Path

from app.services.converter_data_service import ConverterDataService
from app.services.related_converter_service import RelatedConverterService


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"


def test_every_converter_has_four_unique_related_converters() -> None:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    service = RelatedConverterService(converter_data_service)

    converters = converter_data_service.list_active_converters()
    assert converters, "No active converters were found"

    for converter in converters:
        related = service.get_related_converters(converter, limit=4)

        assert len(related) >= 4, f"{converter['slug']} has fewer than 4 related converters"

        slugs = [item["slug"] for item in related]
        assert converter["slug"] not in slugs, f"{converter['slug']} linked to itself"
        assert len(set(slugs)) == len(slugs), f"{converter['slug']} contains duplicate related links"


def test_related_converters_match_input_format_or_cluster() -> None:
    converter_data_service = ConverterDataService(CONVERTERS_DIR)
    service = RelatedConverterService(converter_data_service)

    converter = converter_data_service.load_converter_by_slug("mp4-to-mp3")
    related = service.get_related_converters(converter, limit=4)

    assert any(item.get("source") == converter.get("source") for item in related)
    assert any(item.get("cluster") == converter.get("cluster") for item in related)
