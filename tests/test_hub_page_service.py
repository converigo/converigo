from app.core.registry import ConverterInfo, ConverterRegistry
from app.services.hub_page_service import HubPageService


def test_hub_page_service_builds_expected_hubs_and_assigns_each_converter_once() -> None:
    registry = ConverterRegistry()
    registry.register(
        ConverterInfo(
            id="mp4_to_webm",
            name="MP4 to WebM",
            category="video",
            source_format="mp4",
            target_format="webm",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="png_to_jpg",
            name="PNG to JPG",
            category="image",
            source_format="png",
            target_format="jpg",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="pdf_to_jpg",
            name="PDF to JPG",
            category="pdf",
            source_format="pdf",
            target_format="jpg",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="mp3_to_wav",
            name="MP3 to WAV",
            category="audio",
            source_format="mp3",
            target_format="wav",
            enabled=True,
        )
    )

    service = HubPageService(registry_instance=registry)
    pages = service.build_all()

    assert set(pages) == {"video-converter", "image-converter", "pdf-tools", "audio-tools"}

    converter_ids: list[str] = []
    for page in pages.values():
        assert page["meta"]["title"]
        assert page["meta"]["description"]
        assert page["intro"]["title"]
        assert page["faq"]
        assert page["json_ld"]
        assert page["breadcrumb"]
        assert page["converter_list"]
        assert page["popular_converters"]
        assert page["related_category_section"]
        converter_ids.extend(converter["id"] for converter in page["converter_list"])

    assert converter_ids.count("mp4_to_webm") == 1
    assert converter_ids.count("png_to_jpg") == 1
    assert converter_ids.count("pdf_to_jpg") == 1
    assert converter_ids.count("mp3_to_wav") == 1
