from __future__ import annotations

from typing import Any

from app.services.converter_data_service import ConverterDataService


class HubService:
    def __init__(self, converter_data_service: ConverterDataService) -> None:
        self.converter_data_service = converter_data_service

    def get_hub_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "slug": "image-conversion",
                "path": "/image-conversion",
                "title": "Image Conversion Hub",
                "eyebrow": "Image Conversion",
                "hero_title": "Image Conversion Hub: Optimize, edit, and publish images faster",
                "hero_subtitle": "Explore image workflows, converter tools, and practical resources for web-ready assets, edit-friendly files, compatibility, and icon creation.",
                "description": "Discover workflow-driven image converters and optimization tools for web, editing, compatibility, and icon creation.",
                "keywords": "image conversion hub, image optimization, web image tools, png to jpg, webp converter",
                "all_converters_label": "All image converters",
            },
            {
                "slug": "pdf-conversion",
                "path": "/pdf-conversion",
                "title": "PDF Conversion Hub",
                "eyebrow": "PDF Conversion",
                "hero_title": "PDF Conversion Hub: Convert documents and images with confidence",
                "hero_subtitle": "Move between PDFs and images or documents in a streamlined workflow designed for sharing, archiving, and editing.",
                "description": "Convert PDFs to images or documents, and transform images and documents into portable PDF files with trusted online tools.",
                "keywords": "pdf conversion hub, pdf to image, jpg to pdf, word to pdf",
                "all_converters_label": "All PDF converters",
            },
            {
                "slug": "audio-conversion",
                "path": "/audio-conversion",
                "title": "Audio Conversion Hub",
                "eyebrow": "Audio Conversion",
                "hero_title": "Audio Conversion Hub: Convert music and voice files effortlessly",
                "hero_subtitle": "Switch between audio formats for playback, editing, sharing, and storage without installing software.",
                "description": "Explore audio converters for MP3, WAV, M4A, and other common formats in a single hub.",
                "keywords": "audio conversion hub, mp3 converter, wav converter, audio format conversion",
                "all_converters_label": "All audio converters",
            },
            {
                "slug": "video-conversion",
                "path": "/video-conversion",
                "title": "Video Conversion Hub",
                "eyebrow": "Video Conversion",
                "hero_title": "Video Conversion Hub: Prepare clips for every platform",
                "hero_subtitle": "Convert videos into the right format for sharing, editing, playback, or storage across devices and apps.",
                "description": "Find video converters for MP4, WebM, MOV, AVI, and other essential formats in one place.",
                "keywords": "video conversion hub, mp4 converter, video format conversion, webm converter",
                "all_converters_label": "All video converters",
            },
            {
                "slug": "document-conversion",
                "path": "/document-conversion",
                "title": "Document Conversion Hub",
                "eyebrow": "Document Conversion",
                "hero_title": "Document Conversion Hub: Move documents between formats with ease",
                "hero_subtitle": "Switch documents between common office, archive, and portable formats in a workflow-friendly experience.",
                "description": "Convert documents, office files, and PDFs into the formats you need most with reliable online tools.",
                "keywords": "document conversion hub, word to pdf, pdf to word, office file converter",
                "all_converters_label": "All document converters",
            },
        ]

    def get_hub_definition(self, slug: str) -> dict[str, Any]:
        for hub in self.get_hub_definitions():
            if hub["slug"] == slug:
                return hub
        raise KeyError(f"Unknown hub slug: {slug}")

    def get_hub_page_data(self, slug: str) -> dict[str, Any]:
        hub = self.get_hub_definition(slug)
        all_converters = self.converter_data_service.list_active_converters()
        matching_converters = [
            tool for tool in all_converters if self._matches_hub(tool, slug)
        ]
        matching_converters = self._dedupe_converters(matching_converters)

        featured_converters = [
            tool for tool in matching_converters if tool.get("featured", False)
        ]
        if len(featured_converters) < 3:
            featured_converters.extend(
                [tool for tool in matching_converters if tool not in featured_converters][: 3 - len(featured_converters)]
            )

        popular_converters = [
            tool for tool in matching_converters if tool.get("popular", False)
        ]
        if len(popular_converters) < 4:
            popular_converters.extend(
                [tool for tool in matching_converters if tool not in popular_converters][: 4 - len(popular_converters)]
            )

        related_converters = [
            tool for tool in matching_converters if tool.get("slug") not in {item.get("slug") for item in featured_converters + popular_converters}
        ][:4]

        if not related_converters:
            related_converters = matching_converters[:4]

        return {
            "hub": hub,
            "featured_converters": featured_converters[:3],
            "popular_converters": popular_converters[:4],
            "related_converters": related_converters[:4],
            "all_converters": matching_converters,
            "internal_links": self.list_hub_links(slug),
        }

    def list_hub_links(self, current_slug: str | None = None) -> list[dict[str, Any]]:
        links = []
        for hub in self.get_hub_definitions():
            if current_slug and hub["slug"] == current_slug:
                continue
            links.append(
                {
                    "slug": hub["slug"],
                    "path": hub["path"],
                    "title": hub["title"],
                    "description": hub["description"],
                }
            )
        return links

    def _matches_hub(self, tool: dict[str, Any], slug: str) -> bool:
        category = str(tool.get("category") or "").lower()
        source = str(tool.get("source") or "").lower()
        target = str(tool.get("target") or "").lower()

        if slug == "image-conversion":
            return category == "image" or source in self._image_formats() or target in self._image_formats()

        if slug == "pdf-conversion":
            return "pdf" in {source, target} or category == "pdf"

        if slug == "audio-conversion":
            return source in self._audio_formats() or target in self._audio_formats()

        if slug == "video-conversion":
            return source in self._video_formats() or target in self._video_formats()

        if slug == "document-conversion":
            return category == "document" or source in self._document_formats() or target in self._document_formats()

        return False

    def _dedupe_converters(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped = []
        for tool in tools:
            slug = str(tool.get("slug") or "")
            if not slug or slug in seen:
                continue
            seen.add(slug)
            deduped.append(tool)
        return deduped

    def _image_formats(self) -> set[str]:
        return {"jpg", "jpeg", "png", "webp", "bmp", "gif", "ico", "svg"}

    def _audio_formats(self) -> set[str]:
        return {"mp3", "wav", "flac", "ogg", "m4a", "aac", "opus"}

    def _video_formats(self) -> set[str]:
        return {"mp4", "mov", "avi", "mkv", "webm", "mpeg", "mpg", "wmv"}

    def _document_formats(self) -> set[str]:
        return {"doc", "docx", "pdf", "ppt", "pptx", "xls", "xlsx", "txt", "odt", "rtf"}
