from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, List


class ConverterDataService:

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def _iter_converter_files(self) -> Iterator[Path]:

        if not self.data_dir.exists():
            return iter([])

        files: list[Path] = []

        for path in self.data_dir.iterdir():
            if not path.is_file() or path.suffix.lower() != ".json":
                continue
            if path.name.endswith(".contract.json"):
                continue
            if path.name.endswith(".metadata.json"):
                stem = path.name.removesuffix(".metadata.json")
                if (self.data_dir / f"{stem}.json").exists():
                    continue
                files.append(path)
                continue
            files.append(path)

        return iter(files)

    def _load_converter(
        self,
        path: Path,
    ) -> dict[str, Any]:

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            data = json.load(handle)

        fallback_slug = path.stem
        if path.name.endswith(".metadata.json"):
            fallback_slug = path.name.removesuffix(".metadata.json")

        slug = data.setdefault(
            "slug",
            fallback_slug,
        )

        # --------------------------------------------------
        # Backward Compatibility
        # --------------------------------------------------

        if "source" not in data or "target" not in data:

            parts = slug.split("-to-")

            if len(parts) == 2:

                data.setdefault(
                    "source",
                    parts[0],
                )

                data.setdefault(
                    "target",
                    parts[1],
                )

        data.setdefault(
            "category",
            "general",
        )

        data.setdefault(
            "popular",
            True,
        )

        data.setdefault(
            "featured",
            False,
        )

        data.setdefault(
            "title",
            slug.replace("-", " ").upper(),
        )

        data["cluster"] = self._infer_cluster(data)
        data["output_category"] = self._infer_output_category(data)

        return data

    def list_all_converters(
        self,
    ) -> List[dict[str, Any]]:

        converters = [

            self._load_converter(path)

            for path in self._iter_converter_files()

        ]

        return sorted(

            converters,

            key=lambda tool: tool.get(
                "title",
                "",
            ),

        )

    def list_active_converters(
        self,
    ) -> List[dict[str, Any]]:

        active_converters = []

        for tool in self.list_all_converters():
            active_flag = tool.get("active", tool.get("enabled", True))
            if active_flag is False:
                continue
            active_converters.append(tool)

        return active_converters

    def list_popular_converters(
        self,
        limit: int = 6,
    ) -> List[dict[str, Any]]:

        all_converters = self.list_all_converters()

        def sort_key(tool: dict[str, Any]) -> tuple[Any, ...]:
            featured = tool.get("featured", False)
            popular = tool.get("popular", False)
            sort_order = tool.get("sort_order")
            created_at = tool.get("created_at", "")
            return (
                0 if featured else 1,
                0 if popular else 1,
                sort_order if sort_order is not None else 999999,
                created_at,
                tool.get("title", ""),
            )

        ranked = sorted(
            all_converters,
            key=sort_key,
        )

        popular = [
            tool
            for tool in ranked
            if tool.get("popular", False)
        ]

        if not popular:
            popular = ranked

        return popular[:limit]

    def list_latest_converters(
        self,
        limit: int = 4,
    ) -> List[dict[str, Any]]:

        def sort_key(
            tool: dict[str, Any],
        ) -> str:

            return tool.get(
                "created_at",
                "",
            )

        all_converters = self.list_all_converters()

        sorted_tools = sorted(

            all_converters,

            key=sort_key,

            reverse=True,

        )

        return sorted_tools[:limit]

    def load_converter_by_slug(
        self,
        slug: str,
    ) -> dict[str, Any]:

        normalized = slug.strip().lower()

        for path in self._iter_converter_files():
            stem = path.stem.lower()
            if path.name.lower().endswith(".metadata.json"):
                stem = path.name[: -len(".metadata.json")].lower()

            if stem == normalized:
                return self._load_converter(path)

        raise FileNotFoundError(
            f"Converter definition not found for slug: {slug}"
        )

    def resolve_related_tools(
        self,
        tool_data: dict[str, Any],
        limit: int = 4,
    ) -> List[dict[str, Any]]:

        from app.services.related_converter_service import RelatedConverterService

        service = RelatedConverterService(self)
        return service.get_related_converters(tool_data, limit=limit)

    def _infer_cluster(self, converter: dict[str, Any]) -> str:
        source = str(converter.get("source") or "").lower()
        target = str(converter.get("target") or "").lower()
        if self._is_video(source) and self._is_audio(target):
            return "video-audio"
        if self._is_audio(source) and self._is_video(target):
            return "video-audio"
        if self._is_image(source) and self._is_image(target):
            return "image"
        if self._is_audio(source) and self._is_audio(target):
            return "audio"
        if self._is_video(source) and self._is_video(target):
            return "video"
        if self._is_document(source) and self._is_document(target):
            return "document"
        return str(converter.get("category") or "").lower()

    def _infer_output_category(self, converter: dict[str, Any]) -> str:
        target = str(converter.get("target") or "").lower()
        if self._is_audio(target):
            return "audio"
        if self._is_image(target):
            return "image"
        if self._is_video(target):
            return "video"
        if self._is_document(target):
            return "document"
        return str(converter.get("category") or "").lower()

    def _is_audio(self, value: str) -> bool:
        return value in {"mp3", "wav", "flac", "ogg", "m4a", "aac", "opus"}

    def _is_image(self, value: str) -> bool:
        return value in {"jpg", "jpeg", "png", "webp", "bmp", "gif", "ico", "svg"}

    def _is_video(self, value: str) -> bool:
        return value in {"mp4", "mov", "avi", "mkv", "webm", "mpeg", "mpg", "wmv"}

    def _is_document(self, value: str) -> bool:
        return value in {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "odt", "rtf"}

    def sitemap_entries(
        self,
        base_url: str,
    ) -> List[dict[str, str]]:

        entries = [
            {
                "loc": base_url.rstrip("/") + "/",
                "lastmod": datetime.utcnow().date().isoformat(),
            }
        ]

        trust_pages = ["/about", "/privacy-policy", "/terms", "/contact", "/cookies"]
        for path in trust_pages:
            entries.append(
                {
                    "loc": base_url.rstrip("/") + path,
                    "lastmod": datetime.utcnow().date().isoformat(),
                }
            )

        landing_page_overrides = {
            "mp4-to-mp3": "/mp4-to-mp3",
            "jpg-to-pdf": "/jpg-to-pdf",
            "png-to-jpg": "/png-to-jpg",
            "pdf-to-jpg": "/pdf-to-jpg",
            "png-to-webp": "/png-to-webp",
            "webp-to-png": "/webp-to-png",
        }

        for tool in self.list_active_converters():
            path = landing_page_overrides.get(tool["slug"], f"/tools/{tool['slug']}")
            entries.append(
                {
                    "loc": base_url.rstrip("/") + path,
                    "lastmod": tool.get(
                        "updated_at",
                        tool.get(
                            "created_at",
                            datetime.utcnow().date().isoformat(),
                        ),
                    ),
                }
            )

        return entries