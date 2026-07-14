from __future__ import annotations

from typing import Any

KNOWLEDGE_REQUIRED_SECTIONS: list[str] = [
    "slug",
    "overview",
    "source_format",
    "target_format",
    "advantages",
    "limitations",
    "use_cases",
    "faq",
    "related_converters",
    "internal_links",
    "hub_reference",
]

KNOWLEDGE_SECTION_DEFINITIONS: dict[str, Any] = {
    "slug": {"type": "string"},
    "overview": {"type": "object", "required": ["title", "text"]},
    "source_format": {"type": "object", "required": ["title", "format", "text"]},
    "target_format": {"type": "object", "required": ["title", "format", "text"]},
    "advantages": {"type": "array", "minItems": 1},
    "limitations": {"type": "array", "minItems": 1},
    "use_cases": {"type": "array", "minItems": 1},
    "faq": {"type": "array", "minItems": 1},
    "related_converters": {"type": "array", "minItems": 1},
    "internal_links": {"type": "object", "required": ["title", "items"]},
    "hub_reference": {"type": "object", "required": ["title", "href", "description"]},
}
