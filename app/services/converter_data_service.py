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

        return (
            path
            for path in self.data_dir.iterdir()
            if path.suffix.lower() == ".json"
        )

    def _load_converter(
        self,
        path: Path,
    ) -> dict[str, Any]:

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            data = json.load(handle)

        slug = data.setdefault(
            "slug",
            path.stem,
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

            if path.stem.lower() == normalized:

                return self._load_converter(path)

        raise FileNotFoundError(
            f"Converter definition not found for slug: {slug}"
        )

    def resolve_related_tools(
        self,
        tool_data: dict[str, Any],
        limit: int = 4,
    ) -> List[dict[str, Any]]:

        related_slugs = [

            related.get("slug")

            for related in tool_data.get(
                "related_tools",
                [],
            )

            if related.get("slug")

        ]

        if not related_slugs:

            return self.list_popular_converters(
                limit=limit,
            )

        resolved: List[dict[str, Any]] = []

        for slug in related_slugs:

            try:

                resolved.append(
                    self.load_converter_by_slug(slug)
                )

            except FileNotFoundError:

                continue

        if len(resolved) < limit:

            fallback = [

                tool

                for tool in self.list_popular_converters(
                    limit=limit,
                )

                if tool["slug"] not in related_slugs

            ]

            resolved.extend(

                fallback[
                    : limit - len(resolved)
                ]

            )

        return resolved[:limit]

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

        trust_pages = ["/about", "/privacy", "/terms", "/contact", "/cookies"]
        for path in trust_pages:
            entries.append(
                {
                    "loc": base_url.rstrip("/") + path,
                    "lastmod": datetime.utcnow().date().isoformat(),
                }
            )

        for tool in self.list_active_converters():
            entries.append(
                {
                    "loc": base_url.rstrip("/") + f"/tools/{tool['slug']}",
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