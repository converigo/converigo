from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SeoService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def load_converter_by_slug(self, slug: str) -> dict[str, Any]:
        normalized = slug.strip().lower()
        file_path = self.data_dir / f"{normalized}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Converter definition not found for slug: {slug}")

        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def build_seo_metadata(self, request: Any, tool_data: dict[str, Any]) -> dict[str, str]:
        title = tool_data.get("seo", {}).get("title") or f"{tool_data['title']} | Convertin"
        description = tool_data.get("seo", {}).get("description") or tool_data.get("description", "")
        canonical = tool_data.get("seo", {}).get("canonical") or f"{request.url.scheme}://{request.url.hostname}{request.url.path}"
        return {
            "title": title,
            "description": description,
            "canonical": canonical,
        }
