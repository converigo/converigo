from __future__ import annotations

from typing import Any

from app.core.registry import ConverterRegistry, registry


class HubPageService:
    """Build hub-page content from the converter registry."""

    def __init__(
        self,
        registry_instance: ConverterRegistry | None = None,
    ) -> None:
        self.registry = registry_instance or registry

    def build_all(self) -> dict[str, dict[str, Any]]:
        hub_definitions = {
            "video-converter": {
                "title": "Video Conversion Hub",
                "description": "Convert videos into the formats you need for sharing, editing, and playback.",
                "intro": {
                    "title": "Video conversion made simple",
                    "text": "Find the right converter for your video workflow in one place.",
                },
                "faq": [
                    {
                        "question": "What is a video converter?",
                        "answer": "Use it to switch between common video formats without installing software.",
                    }
                ],
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Video Converter", "url": "/video-converter"}],
            },
            "image-converter": {
                "title": "Image Conversion Hub",
                "description": "Convert images for web use, editing, compatibility, and sharing.",
                "intro": {
                    "title": "Image conversion workflows",
                    "text": "Choose from fast tools that cover common image formats and use cases.",
                },
                "faq": [
                    {
                        "question": "Why use an image converter?",
                        "answer": "It helps you adapt images for websites, documents, and editing workflows.",
                    }
                ],
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Image Converter", "url": "/image-converter"}],
            },
            "pdf-tools": {
                "title": "PDF Tools Hub",
                "description": "Work with PDFs and related document conversion flows in one hub.",
                "intro": {
                    "title": "PDF and document conversion",
                    "text": "Move files between PDF, image, and document formats quickly.",
                },
                "faq": [
                    {
                        "question": "What are PDF tools?",
                        "answer": "They cover common conversions involving PDF files and related formats.",
                    }
                ],
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "PDF Tools", "url": "/pdf-tools"}],
            },
            "audio-tools": {
                "title": "Audio Tools Hub",
                "description": "Convert and manage audio files for playback, editing, and sharing.",
                "intro": {
                    "title": "Audio conversion workflows",
                    "text": "Find the right tool for common audio format changes.",
                },
                "faq": [
                    {
                        "question": "What do audio tools do?",
                        "answer": "They help convert audio files between common formats without extra software.",
                    }
                ],
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Audio Tools", "url": "/audio-tools"}],
            },
            "archive-tools": {
                "title": "Archive Tools Hub",
                "description": "Extract, merge, and compress archive files with fast browser-based tools.",
                "intro": {
                    "title": "Archive file workflows",
                    "text": "Find the right tool to open, compress, or convert archive formats quickly.",
                },
                "faq": [
                    {
                        "question": "What are archive tools?",
                        "answer": "Use them to manage compressed and packaged files like ZIP, RAR, TAR, and 7Z.",
                    }
                ],
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Archive Tools", "url": "/archive-tools"}],
            },
        }

        pages: dict[str, dict[str, Any]] = {}
        for slug, definition in hub_definitions.items():
            converters = self._select_converters(slug)
            if not converters:
                continue

            pages[slug] = {
                "slug": slug,
                "meta": {
                    "title": f"{definition['title']} | Converigo",
                    "description": definition["description"],
                },
                "intro": definition["intro"],
                "faq": definition["faq"],
                "json_ld": {
                    "@context": "https://schema.org",
                    "@type": "CollectionPage",
                    "name": definition["title"],
                    "description": definition["description"],
                },
                "breadcrumb": definition["breadcrumb"],
                "converter_list": [self._serialize_converter(converter) for converter in converters],
                "popular_converters": [self._serialize_converter(converter) for converter in converters[:2]],
                "related_category_section": {
                    "title": "Related categories",
                    "items": [
                        {"title": "Video tools", "href": "/video-converter"},
                        {"title": "Image tools", "href": "/image-converter"},
                        {"title": "PDF tools", "href": "/pdf-tools"},
                        {"title": "Audio tools", "href": "/audio-tools"},
                        {"title": "Archive tools", "href": "/archive-tools"},
                    ],
                },
            }
        return pages

    def _select_converters(self, slug: str) -> list[Any]:
        active_converters = [converter for converter in self.registry.get_all() if getattr(converter, "enabled", True)]
        if slug == "video-converter":
            return [converter for converter in active_converters if str(getattr(converter, "category", "")).lower() == "video"]
        if slug == "image-converter":
            return [converter for converter in active_converters if str(getattr(converter, "category", "")).lower() == "image"]
        if slug == "pdf-tools":
            return [converter for converter in active_converters if str(getattr(converter, "category", "")).lower() in {"pdf", "document"}]
        if slug == "audio-tools":
            return [converter for converter in active_converters if str(getattr(converter, "category", "")).lower() == "audio"]
        if slug == "archive-tools":
            return [converter for converter in active_converters if str(getattr(converter, "category", "")).lower() == "archive"]
        return []

    def _serialize_converter(self, converter: Any) -> dict[str, Any]:
        return {
            "id": getattr(converter, "id", ""),
            "name": getattr(converter, "name", ""),
            "category": getattr(converter, "category", ""),
        }
