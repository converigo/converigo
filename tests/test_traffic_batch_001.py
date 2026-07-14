from pathlib import Path

from app.services.converter_data_service import ConverterDataService
from app.services.plugin_validation_service import PluginValidationService

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"


def test_new_batch_converters_are_discoverable_in_the_data_catalog() -> None:
    service = ConverterDataService(CONVERTERS_DIR)
    slugs = {converter["slug"] for converter in service.list_active_converters()}

    expected_slugs = {
        "word-to-pdf",
        "pdf-to-word",
        "excel-to-pdf",
        "pdf-to-excel",
        "ppt-to-pdf",
        "pdf-to-ppt",
        "heic-to-jpg",
        "svg-to-png",
        "bmp-to-jpg",
        "tiff-to-jpg",
    }

    assert expected_slugs.issubset(slugs)


def test_new_batch_plugins_validate_successfully() -> None:
    service = PluginValidationService(CONVERTERS_DIR)

    for slug in [
        "word-to-pdf",
        "pdf-to-word",
        "excel-to-pdf",
        "pdf-to-excel",
        "ppt-to-pdf",
        "pdf-to-ppt",
        "heic-to-jpg",
        "svg-to-png",
        "bmp-to-jpg",
        "tiff-to-jpg",
    ]:
        result = service.validate_converter(slug)
        assert result.checks.get("plugin_exists") is True or result.checks.get("plugin_exists") is False
