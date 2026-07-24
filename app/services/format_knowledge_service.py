from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.knowledge_schema import validate_format_knowledge


class FormatKnowledgeService:
    """Load and validate format knowledge enrichment payloads."""

    def __init__(self, format_knowledge_dir: Path | str | None = None) -> None:
        self.format_knowledge_dir = Path(format_knowledge_dir or "app/data/format_knowledge")

    def build_enrichment(self, format_name: str) -> dict[str, Any] | None:
        normalized = str(format_name or "").strip().lower()
        if not normalized:
            raise ValueError("format_name is required")

        file_path = self.format_knowledge_dir / f"{normalized}.json"
        if not file_path.exists():
            raise OSError(f"Format knowledge file not found: {file_path}")

        payload = self._load_json(file_path)
        if not isinstance(payload, dict):
            raise ValueError("Format knowledge payload must be an object")

        errors = validate_format_knowledge(payload)
        if errors:
            raise ValueError(f"Invalid format knowledge payload for '{normalized}': {errors}")

        return {"format_knowledge": payload}

    def _load_json(self, file_path: Path) -> Any:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in format knowledge file: {file_path}") from exc
        except OSError as exc:
            raise OSError(f"Unable to read format knowledge file: {file_path}") from exc
