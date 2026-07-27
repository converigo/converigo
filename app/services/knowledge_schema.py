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

# ---------------------------------------------------------------------------
# Format knowledge hub schema
# ---------------------------------------------------------------------------
# These sections define the knowledge content structure for format pages.
# Unlike the converter-oriented knowledge schema above, this schema is
# format-specific and designed to enrich format encyclopedia pages.

FORMAT_KNOWLEDGE_REQUIRED_FIELDS: list[str] = [
    "slug",
    "name",
    "quick_answer",
    "definition",
    "use_cases",
    "advantages",
    "limitations",
    "comparisons",
    "related_tools",
    "faq",
]

FORMAT_KNOWLEDGE_FIELD_DEFINITIONS: dict[str, Any] = {
    "slug": {"type": "string", "description": "Format identifier, e.g. 'pdf'"},
    "name": {"type": "string", "description": "Display name, e.g. 'PDF'"},
    "quick_answer": {"type": "string", "description": "One-sentence summary for SEO snippets"},
    "definition": {"type": "string", "description": "In-depth definition of the format"},
    "use_cases": {"type": "array", "minItems": 1, "item_type": "object", "required": ["title", "text"]},
    "advantages": {"type": "array", "minItems": 1, "item_type": "object", "required": ["title", "text"]},
    "limitations": {"type": "array", "minItems": 1, "item_type": "object", "required": ["title", "text"]},
    "comparisons": {"type": "array", "minItems": 1, "item_type": "object", "required": ["title", "text"]},
    "related_tools": {"type": "array", "minItems": 1, "item_type": "object", "required": ["slug", "title", "description", "href"]},
    "faq": {"type": "array", "minItems": 1, "item_type": "object", "required": ["question", "answer"]},
}


def validate_format_knowledge(data: dict[str, Any]) -> list[str]:
    """Validate a format knowledge payload against the schema.
    Returns a list of missing or invalid field names (empty if valid).
    """
    errors: list[str] = []
    for field in FORMAT_KNOWLEDGE_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
            continue
        value = data[field]
        definition = FORMAT_KNOWLEDGE_FIELD_DEFINITIONS.get(field, {})
        field_type = definition.get("type", "string")

        if field_type == "string" and (not isinstance(value, str) or not value.strip()):
            errors.append(f"Field '{field}' must be a non-empty string")
        elif field_type == "array":
            if not isinstance(value, list) or len(value) < 1:
                errors.append(f"Field '{field}' must be a non-empty array")
            else:
                item_required = definition.get("required", [])
                for idx, item in enumerate(value):
                    for req in item_required:
                        if req not in item or not item[req]:
                            errors.append(f"Field '{field}[{idx}]' missing required key '{req}'")

    return errors
