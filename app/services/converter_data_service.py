from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, List

from app.services.converter_registry_service import ConverterRegistryService


NON_PRODUCTION_READY_SLUGS = {
    "svg-to-png",
    "svg-to-pdf",
    "heic-to-jpg",
    "heif-to-jpeg",
    "7z-extract",
}


def _is_production_ready(contract: dict[str, Any] | None) -> bool:
    if contract is None:
        return False

    lifecycle_status = str(contract.get("lifecycle_status", "")).strip().lower()
    if lifecycle_status != "active":
        return False

    return True


class ConverterDataService:

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.contracts_dir = data_dir
        self._contract_registry_service: ConverterRegistryService | None = None

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
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        fallback_slug = path.stem
        if path.name.endswith(".metadata.json"):
            fallback_slug = path.name.removesuffix(".metadata.json")

        slug = data.setdefault("slug", fallback_slug)

        if "source" not in data or "target" not in data:
            parts = slug.split("-to-")
            if len(parts) == 2:
                data.setdefault("source", parts[0])
                data.setdefault("target", parts[1])

        data.setdefault("category", "general")
        data.setdefault("popular", True)
        data.setdefault("featured", False)
        data.setdefault("title", slug.replace("-", " ").upper())
        data.setdefault("active", True)
        data.setdefault("public", self._is_publicly_visible(slug))

        data["cluster"] = self._infer_cluster(data)
        data["output_category"] = self._infer_output_category(data)

        return data

    def list_all_converters(
        self,
    ) -> List[dict[str, Any]]:
        converters = [self._load_converter(path) for path in self._iter_converter_files()]
        return sorted(converters, key=lambda tool: tool.get("title", ""))

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

    def list_public_converters(self) -> List[dict[str, Any]]:
        """
        Return list of public converters that are:
        - Marked as active
        - Have an active contract in the registry
        - Publicly visible (not in blocklist)
        
        This ensures recommendations only include valid, production-ready converters.
        """
        public_converters = []
        active_contract_slugs = self._get_active_contract_slugs()
        has_active_contracts = len(active_contract_slugs) > 0

        for tool in self.list_all_converters():
            slug = str(tool.get("slug", "")).strip().lower()
            if not slug:
                continue

            # If there are active contracts, require membership; otherwise
            # allow converters determined solely by their own metadata.
            if has_active_contracts and slug not in active_contract_slugs:
                continue

            # Require: marked as publicly visible only when active contracts exist.
            if has_active_contracts and not self._is_publicly_visible(slug):
                continue
            public_converters.append(tool)

        return public_converters

    def list_popular_converters(
        self,
        limit: int = 6,
    ) -> List[dict[str, Any]]:
        all_converters = self.list_active_converters()

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

        ranked = sorted(all_converters, key=sort_key)
        popular = [tool for tool in ranked if tool.get("popular", False)]
        if not popular:
            popular = ranked
        return popular[:limit]

    def list_latest_converters(
        self,
        limit: int = 4,
    ) -> List[dict[str, Any]]:
        def sort_key(tool: dict[str, Any]) -> str:
            return tool.get("created_at", "")

        all_converters = self.list_active_converters()
        sorted_tools = sorted(all_converters, key=sort_key, reverse=True)
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

        raise FileNotFoundError(f"Converter definition not found for slug: {slug}")

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

    def _get_active_contract_slugs(self) -> set[str]:
        return {
            str(contract.get("slug", "")).strip().lower()
            for contract in self._get_contract_registry().get_active()
        }

    def _is_publicly_visible(self, slug: str) -> bool:
        normalized_slug = str(slug or "").strip().lower()
        if not normalized_slug:
            return False

        contract = self._get_contract_registry().get_by_slug(normalized_slug)
        if not _is_production_ready(contract):
            return False

        return normalized_slug not in NON_PRODUCTION_READY_SLUGS

    def _get_contract_registry(self) -> ConverterRegistryService:
        if self._contract_registry_service is None:
            self._contract_registry_service = ConverterRegistryService(self.contracts_dir)
        return self._contract_registry_service
