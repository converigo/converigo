from __future__ import annotations

from typing import Any

from app.services.converter_registry_service import ConverterRegistryService
from app.services.knowledge_schema import KNOWLEDGE_REQUIRED_SECTIONS


class KnowledgeService:
    """Generate deterministic educational Knowledge Objects from converter contracts."""

    REQUIRED_SECTIONS = set(
        KNOWLEDGE_REQUIRED_SECTIONS
        + [
            "what_is_source",
            "what_is_target",
            "differences",
            "best_practices",
            "common_mistakes",
            "tips",
            "faq_enrichment",
            "glossary",
        ]
    )

    HUB_SLUG_BY_CATEGORY = {
        "video": "video-converter",
        "image": "image-converter",
        "pdf": "pdf-tools",
        "document": "pdf-tools",
        "audio": "audio-tools",
        "archive": "archive-tools",
    }

    HUB_TITLES = {
        "video-converter": "Video Conversion Hub",
        "image-converter": "Image Conversion Hub",
        "pdf-tools": "PDF Tools Hub",
        "audio-tools": "Audio Tools Hub",
        "archive-tools": "Archive Tools Hub",
    }

    HUB_DESCRIPTIONS = {
        "video-converter": "Convert videos into the formats you need for sharing, editing, and playback.",
        "image-converter": "Convert images for web use, editing, compatibility, and sharing.",
        "pdf-tools": "Work with PDFs and related document conversion flows in one hub.",
        "audio-tools": "Convert and manage audio files for playback, editing, and sharing.",
        "archive-tools": "Extract, merge, and compress archive files with fast browser-based tools.",
    }

    def __init__(self, contracts_dir: str | Any) -> None:
        self.registry = ConverterRegistryService(contracts_dir)

    def generate_payload(self, contract: dict[str, Any]) -> dict[str, Any]:
        slug = str(contract.get("slug", "")).strip()
        name = str(contract.get("name", slug or "Converter")).strip()
        description = str(contract.get("description", "")).strip()
        source_formats = [str(item).strip().upper() for item in contract.get("input_formats", []) if str(item).strip()]
        target_formats = [str(item).strip().upper() for item in contract.get("output_formats", []) if str(item).strip()]
        source_label = source_formats[0] if source_formats else "SOURCE"
        target_label = target_formats[0] if target_formats else "TARGET"
        source_name = source_label.lower()
        target_name = target_label.lower()
        category = str(contract.get("category", "")).strip().lower()

        payload = {
            "slug": slug,
            "overview": self._build_overview(name, description, source_label, target_label),
            "source_format": self._build_format_section("Source format", source_label, f"{source_label} is the input format used by this converter."),
            "target_format": self._build_format_section("Target format", target_label, f"{target_label} is the output format produced by this converter."),
            "advantages": self._build_advantages(source_name, target_name),
            "limitations": self._build_limitations(source_name, target_name),
            "use_cases": self._build_use_cases(name, source_label, target_label),
            "faq": self._build_faq(name, source_label, target_label),
            "faq_enrichment": self._build_faq(name, source_label, target_label),
            "related_converters": self._build_related_converters(contract, limit=4),
            "internal_links": self._build_internal_links(contract, source_label, target_label),
            "hub_reference": self._build_hub_reference(category),
            "what_is_source": {
                "title": f"What is {source_label}?",
                "text": f"{source_label} is the source format used in the {name} conversion workflow.",
            },
            "what_is_target": {
                "title": f"What is {target_label}?",
                "text": f"{target_label} is the output format produced by the {name} process.",
            },
            "differences": [
                {
                    "title": "Format structure",
                    "text": f"{source_label} and {target_label} differ in how they store and represent data.",
                },
                {
                    "title": "Use case",
                    "text": f"{source_label} is usually the starting point, while {target_label} is better suited for the chosen output workflow.",
                },
            ],
            "best_practices": [
                {
                    "title": "Use a clean source file",
                    "text": f"Start with a clean {source_name} file to get the best {target_name} result.",
                },
                {
                    "title": "Check the output",
                    "text": "Review the converted file to make sure it matches your expectations.",
                },
            ],
            "common_mistakes": [
                {
                    "title": "Uploading the wrong file",
                    "text": f"Make sure the file you upload is actually in {source_label} format.",
                },
                {
                    "title": "Ignoring file size",
                    "text": "Very large files may require more time or a retry if the process times out.",
                },
            ],
            "tips": [
                {
                    "title": "Keep a backup",
                    "text": f"Save the original {source_name} file before converting it.",
                },
                {
                    "title": "Choose the right preset",
                    "text": f"Pick the {target_name} option that fits your workflow.",
                },
            ],
            "glossary": [
                {
                    "term": source_label,
                    "definition": f"The input format used by this converter.",
                },
                {
                    "term": target_label,
                    "definition": f"The output format generated by this converter.",
                },
            ],
        }

        self.validate_payload(payload)
        return payload

    def generate_all(self) -> dict[str, dict[str, Any]]:
        payloads: dict[str, dict[str, Any]] = {}
        for contract in self.registry.get_active():
            slug = str(contract.get("slug", "")).strip()
            if not slug:
                continue
            payloads[slug] = self.generate_payload(contract)
        return dict(sorted(payloads.items(), key=lambda item: item[0]))

    def validate_payload(self, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        missing_sections = []
        for section in sorted(self.REQUIRED_SECTIONS):
            value = payload.get(section)
            if section == "overview":
                if not isinstance(value, dict) or not value.get("title") or not value.get("text"):
                    missing_sections.append(section)
            elif section in {"source_format", "target_format"}:
                if not isinstance(value, dict) or not value.get("title") or not value.get("format") or not value.get("text"):
                    missing_sections.append(section)
            elif section in {"advantages", "limitations", "use_cases", "faq", "related_converters", "faq_enrichment", "glossary", "differences", "best_practices", "common_mistakes", "tips"}:
                if not isinstance(value, list) or not value:
                    missing_sections.append(section)
            elif section == "internal_links":
                if not isinstance(value, dict) or not value.get("title") or not isinstance(value.get("items"), list) or not value["items"]:
                    missing_sections.append(section)
            elif section == "hub_reference":
                if not isinstance(value, dict) or not value.get("title") or not value.get("href") or not value.get("description"):
                    missing_sections.append(section)
            else:
                if not value:
                    missing_sections.append(section)
        if missing_sections:
            raise ValueError(f"Knowledge payload missing required sections: {', '.join(missing_sections)}")

    def _build_overview(self, name: str, description: str, source_label: str, target_label: str) -> dict[str, str]:
        doc = description or f"Use this converter to transform {source_label} files into {target_label} output quickly and reliably."
        return {
            "title": f"Overview of {name}",
            "text": doc,
        }

    def _build_format_section(self, title: str, format_label: str, text: str) -> dict[str, str]:
        return {
            "title": title,
            "format": format_label,
            "text": text,
        }

    def _build_advantages(self, source_name: str, target_name: str) -> list[dict[str, str]]:
        return [
            {
                "title": "Fast conversion",
                "text": f"Convert {source_name} files to {target_name} with a quick and simple process.",
            },
            {
                "title": "Wide compatibility",
                "text": f"The output is compatible with common {target_name} workflows.",
            },
        ]

    def _build_limitations(self, source_name: str, target_name: str) -> list[dict[str, str]]:
        return [
            {
                "title": "Source quality matters",
                "text": f"The quality of the converted {target_name} file depends on the original {source_name} source.",
            },
            {
                "title": "Size and complexity",
                "text": "Very large or complex files may take longer to process.",
            },
        ]

    def _build_use_cases(self, name: str, source_label: str, target_label: str) -> list[dict[str, str]]:
        return [
            {
                "title": f"Convert {source_label} files for sharing",
                "text": f"Use {name} when you need a {target_label} file that is easy to share or publish.",
            },
            {
                "title": f"Prepare {target_label} files for editing",
                "text": f"Use this converter when you want to turn {source_label} source material into editable {target_label} output.",
            },
            {
                "title": "Standardize file workflows",
                "text": f"Use the converter to move between formats in a consistent, repeatable workflow.",
            },
        ]

    def _build_faq(self, name: str, source_label: str, target_label: str) -> list[dict[str, str]]:
        return [
            {
                "question": f"What does {name} do?",
                "answer": f"It converts {source_label} files into {target_label} output in a browser-based workflow.",
            },
            {
                "question": f"Which files can I convert?",
                "answer": f"This tool supports {source_label} source files and produces {target_label} output.",
            },
            {
                "question": "Is the conversion fast?",
                "answer": "Yes, it is designed to produce results quickly for everyday tasks.",
            },
            {
                "question": "Can I use this on mobile?",
                "answer": "Yes, the converter works in modern browsers on desktop and mobile devices.",
            },
            {
                "question": "What if the conversion fails?",
                "answer": "Try a fresh upload, confirm the source format, and retry the process.",
            },
            {
                "question": "Will the file quality be preserved?",
                "answer": "The converter aims to preserve as much quality as possible while producing the chosen output format.",
            },
        ]

    def _build_related_converters(self, contract: dict[str, Any], limit: int = 4) -> list[dict[str, str]]:
        current_slug = str(contract.get("slug", "")).strip()
        current_category = str(contract.get("category", "")).strip().lower()
        current_input = str((contract.get("input_formats") or [""])[0]).strip().lower()
        current_output = str((contract.get("output_formats") or [""])[0]).strip().lower()

        candidates: list[tuple[int, dict[str, str]]] = []
        for candidate in self.registry.get_active():
            slug = str(candidate.get("slug", "")).strip()
            if not slug or slug == current_slug:
                continue

            score = 0
            candidate_category = str(candidate.get("category", "")).strip().lower()
            candidate_input = str((candidate.get("input_formats") or [""])[0]).strip().lower()
            candidate_output = str((candidate.get("output_formats") or [""])[0]).strip().lower()

            if candidate_category == current_category:
                score += 4
            if candidate_input and candidate_input == current_input:
                score += 3
            if candidate_output and candidate_output == current_output:
                score += 2
            if current_output and candidate_output and candidate_output == current_output:
                score += 1

            candidates.append((score, {
                "slug": slug,
                "title": str(candidate.get("name", slug)).strip(),
                "description": str(candidate.get("description", "Discover another conversion flow.")).strip(),
                "href": f"/tools/{slug}",
            }))

        ordered = [item for score, item in sorted(candidates, key=lambda item: (-item[0], item[1]["title"]))]
        if len(ordered) < limit:
            fallback = [
                {
                    "slug": str(candidate.get("slug", "")).strip(),
                    "title": str(candidate.get("name", "Converter")).strip(),
                    "description": str(candidate.get("description", "Discover another conversion flow.")).strip(),
                    "href": f"/tools/{str(candidate.get('slug', '')).strip()}",
                }
                for candidate in self.registry.get_active()
                if str(candidate.get("slug", "")).strip() != current_slug
            ]
            for item in fallback:
                if item["slug"] not in {entry["slug"] for entry in ordered}:
                    ordered.append(item)
                if len(ordered) >= limit:
                    break

        if not ordered:
            hub_reference = self._build_hub_reference(current_category)
            ordered.append(
                {
                    "slug": f"{current_category}-hub",
                    "title": f"Explore related {current_category or 'conversion'} tools",
                    "description": f"Browse related converters and tools in the {hub_reference['title']}.",
                    "href": hub_reference["href"],
                }
            )

        return ordered[:limit]

    def _build_internal_links(self, contract: dict[str, Any], source_label: str, target_label: str) -> dict[str, Any]:
        landing_path = str(contract.get("landing_path") or "").strip() or f"/tools/{contract.get('slug', '')}"
        hub_reference = self._build_hub_reference(str(contract.get("category", "")).strip().lower())

        return {
            "title": "Related resources",
            "items": [
                {
                    "title": f"Open the {source_label} to {target_label} converter",
                    "href": landing_path,
                    "description": f"Start the conversion process on the converter landing page.",
                },
                {
                    "title": hub_reference["title"],
                    "href": hub_reference["href"],
                    "description": hub_reference["description"],
                },
            ],
        }

    def _build_hub_reference(self, category: str) -> dict[str, str]:
        hub_slug = self.HUB_SLUG_BY_CATEGORY.get(category, "pdf-tools")
        title = self.HUB_TITLES.get(hub_slug, "Conversion Hub")
        description = self.HUB_DESCRIPTIONS.get(hub_slug, "Explore related conversion tools in the hub.")
        href = f"/{hub_slug}"
        return {
            "title": title,
            "href": href,
            "description": description,
        }
