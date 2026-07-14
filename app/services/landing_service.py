from __future__ import annotations

from typing import Any

from app.services.converter_data_service import ConverterDataService
from app.services.seo_service import SeoService


class LandingContractError(ValueError):
    """Raised when a landing payload is missing a required contract section."""


class LandingPageBuilder:
    REQUIRED_SECTIONS = {
        "h1",
        "seo_title",
        "meta_description",
        "intro",
        "steps",
        "benefits",
        "supported_formats",
        "tips",
        "common_problems",
        "faq",
        "json_ld",
        "breadcrumb",
        "cta",
        "download",
        "related_converter",
        "related_converters",
        "internal_links",
    }

    def __init__(self, seo_service: SeoService, converter_data_service: ConverterDataService) -> None:
        self.seo_service = seo_service
        self.converter_data_service = converter_data_service

    def validate_contract(self, landing: dict[str, Any]) -> None:
        missing_sections = []
        for section in sorted(self.REQUIRED_SECTIONS):
            value = landing.get(section)
            if section == "intro":
                if not isinstance(value, dict) or not value.get("title") or not value.get("text"):
                    missing_sections.append(section)
            elif section in {"steps", "benefits", "tips", "common_problems"}:
                if not isinstance(value, list) or not value:
                    missing_sections.append(section)
            elif section == "faq":
                if not isinstance(value, list) or not value or len(value) < 8:
                    missing_sections.append(section)
            elif section == "breadcrumb":
                if not isinstance(value, list) or not value:
                    missing_sections.append(section)
            elif section == "cta":
                if not isinstance(value, dict) or not value.get("title") or not value.get("text"):
                    missing_sections.append(section)
            elif section == "download":
                if not isinstance(value, dict) or not value.get("title") or not value.get("text"):
                    missing_sections.append(section)
            elif section == "supported_formats":
                if not isinstance(value, dict) or not value.get("input") or not value.get("output"):
                    missing_sections.append(section)
            elif section == "related_converter":
                if not isinstance(value, dict) or not value.get("title"):
                    missing_sections.append(section)
            elif section == "related_converters":
                if not isinstance(value, list) or not value:
                    missing_sections.append(section)
            elif section == "internal_links":
                if not isinstance(value, dict) or not value.get("title") or not isinstance(value.get("items"), list):
                    missing_sections.append(section)
            elif section == "json_ld":
                if not isinstance(value, dict) or not value:
                    missing_sections.append(section)
            else:
                if not value:
                    missing_sections.append(section)

        if missing_sections:
            raise LandingContractError(f"Landing contract missing required sections: {', '.join(missing_sections)}")

    def _normalize_format_name(self, value: Any) -> str:
        text = str(value or "").strip().upper()
        return text or "FILE"

    def _source_target_names(self, tool_data: dict[str, Any]) -> tuple[str, str]:
        source_name = (tool_data.get("source") or "file").lower()
        target_name = (tool_data.get("target") or "output").lower()
        return source_name, target_name

    def _build_intro(self, tool_data: dict[str, Any]) -> dict[str, str]:
        source_name, target_name = self._source_target_names(tool_data)
        title = f"How to convert {source_name.upper()} to {target_name.upper()}"
        if tool_data.get("slug") == "mp4-to-mp3":
            title = "How to convert MP4 to MP3"
        text = (
            tool_data.get("landing", {}).get("intro")
            or f"Use this converter to turn {source_name} files into {target_name} output in seconds."
        )
        return {"title": title, "text": text}

    def _build_steps(self, tool_data: dict[str, Any]) -> list[dict[str, str]]:
        source_name, target_name = self._source_target_names(tool_data)
        return [
            {
                "title": "Upload your file",
                "description": f"Select a {source_name} file from your device to start the conversion.",
            },
            {
                "title": "Choose the output format",
                "description": f"Pick {target_name} as the result format and review the conversion options.",
            },
            {
                "title": "Download the converted file",
                "description": "Get the finished result instantly, ready to share or keep in your workflow.",
            },
        ]

    def _build_benefits(self, tool_data: dict[str, Any]) -> list[dict[str, str]]:
        existing = tool_data.get("benefits") or []
        if isinstance(existing, list) and existing:
            normalized = []
            for item in existing:
                if isinstance(item, dict):
                    normalized.append(
                        {
                            "title": str(item.get("title") or "Fast conversion").strip(),
                            "text": str(item.get("text") or "").strip(),
                        }
                    )
            if normalized:
                return normalized

        source_name, target_name = self._source_target_names(tool_data)
        return [
            {
                "title": "Fast conversion",
                "text": f"Convert {source_name} files to {target_name} quickly and securely.",
            },
            {
                "title": "Reliable output",
                "text": "Receive a polished result that is ready for sharing and immediate use.",
            },
            {
                "title": "No installation required",
                "text": "Use the converter directly in the browser without downloading extra software.",
            },
        ]

    def _build_supported_formats(self, tool_data: dict[str, Any]) -> dict[str, Any]:
        provided = tool_data.get("supported_formats") or {}
        if isinstance(provided, dict):
            input_formats = list(provided.get("input") or [])
            output_formats = list(provided.get("output") or [])
            description = str(provided.get("description") or "").strip()
            if not input_formats and not output_formats:
                return self._build_supported_formats_from_names(tool_data)
            return {
                "input": [self._normalize_format_name(item) for item in input_formats],
                "output": [self._normalize_format_name(item) for item in output_formats],
                "description": description or f"{self._normalize_format_name(input_formats[0] if input_formats else tool_data.get('source'))} input, {self._normalize_format_name(output_formats[0] if output_formats else tool_data.get('target'))} output",
            }

        if isinstance(provided, list):
            return {
                "input": [self._normalize_format_name(item) for item in provided],
                "output": [],
                "description": "Supported file formats depend on the selected converter flow.",
            }

        return self._build_supported_formats_from_names(tool_data)

    def _build_supported_formats_from_names(self, tool_data: dict[str, Any]) -> dict[str, Any]:
        source_name, target_name = self._source_target_names(tool_data)
        return {
            "input": [self._normalize_format_name(source_name)],
            "output": [self._normalize_format_name(target_name)],
            "description": f"{source_name.upper()} input, {target_name.upper()} output",
        }

    def _build_tips(self, tool_data: dict[str, Any]) -> list[dict[str, str]]:
        source_name, target_name = self._source_target_names(tool_data)
        return [
            {
                "title": "Keep a backup",
                "text": f"Save your original {source_name} file before you begin a conversion.",
            },
            {
                "title": "Choose the right preset",
                "text": f"Select a {target_name} preset that matches your downstream workflow.",
            },
            {
                "title": "Check the result",
                "text": "Open the downloaded file to confirm that the conversion looks correct.",
            },
        ]

    def _build_common_problems(self, tool_data: dict[str, Any]) -> list[dict[str, str]]:
        source_name, target_name = self._source_target_names(tool_data)
        return [
            {
                "title": "File not accepted",
                "text": f"Use a supported {source_name.upper()} file and confirm the upload size before trying again.",
            },
            {
                "title": "Output looks different than expected",
                "text": f"Try a different {target_name.upper()} preset or re-upload the source file if the result is incomplete.",
            },
            {
                "title": "Conversion is slow",
                "text": "Large files can take a little longer, but the process should finish without extra steps.",
            },
        ]

    def _prepare_faq(self, tool_data: dict[str, Any], faq_items: list[dict[str, str]] | None) -> list[dict[str, str]]:
        label = tool_data.get("title", "").replace(" Converter", "").strip()
        slug = str(tool_data.get("slug", "")).strip()
        source_name, target_name = self._source_target_names(tool_data)

        fallback_faq: list[dict[str, str]] = [
            {
                "question": f"What is {label or 'this'} conversion?",
                "answer": f"Use this converter to transform {label or 'your files'} quickly and securely.",
            },
            {
                "question": f"How do I convert {source_name.upper()} to {target_name.upper()}?",
                "answer": "Upload your file, choose the output format, and download the converted result.",
            },
            {
                "question": f"Is the {label or 'converter'} free to use?",
                "answer": "Yes, this converter is free for standard conversion tasks.",
            },
            {
                "question": "Will the output preserve quality?",
                "answer": "The converter uses reliable processing so the result stays ready for everyday use.",
            },
            {
                "question": "What file sizes are supported?",
                "answer": "Supported sizes depend on the file type and the selected conversion flow.",
            },
            {
                "question": "Can I convert files on mobile?",
                "answer": "Yes, the tool works in modern browsers on desktop and mobile devices.",
            },
            {
                "question": "What if the conversion fails?",
                "answer": "Try a fresh upload, confirm the source format, and retry the conversion.",
            },
            {
                "question": "Which formats are compatible?",
                "answer": "The tool supports the source and output formats listed on the landing page.",
            },
        ]

        if slug.endswith("-png") or slug.endswith("-to-png"):
            fallback_faq.append(
                {
                    "question": "Does PNG preserve image quality?",
                    "answer": "PNG uses lossless compression, so image quality stays intact during conversion.",
                }
            )

        faq = []
        seen_questions: set[str] = set()
        for item in [*fallback_faq, *(faq_items or tool_data.get("faq", []) or [])]:
            question = str(item.get("question", "")).strip()
            if not question:
                continue
            question_key = question.lower()
            if question_key in seen_questions:
                continue
            seen_questions.add(question_key)
            faq.append(
                {
                    "question": question,
                    "answer": str(item.get("answer") or "").strip() or "This converter keeps the process simple and dependable.",
                }
            )

        while len(faq) < 8:
            faq.append(
                {
                    "question": f"How do I use this {label or 'converter'}?",
                    "answer": "Upload the file, choose the output format, and download the converted result.",
                }
            )

        return faq[:12]

    def _build_breadcrumb(self, tool_data: dict[str, Any], canonical_path: str | None) -> list[dict[str, str]]:
        slug = tool_data.get("slug", "")
        path = canonical_path or f"/tools/{slug}"
        title = tool_data.get("title") or slug.replace("-", " ").title()
        return [
            {"name": "Home", "url": "/"},
            {"name": title, "url": path},
        ]

    def _build_download_section(self, tool_data: dict[str, Any]) -> dict[str, str]:
        target_name = (tool_data.get("target") or "output").upper()
        if tool_data.get("slug") == "mp4-to-mp3":
            title = "Download your converted MP3"
            text = "Once conversion completes, download the MP3 file instantly and keep using it in your workflow."
        else:
            title = f"Download your converted {target_name}"
            text = f"The converted {target_name} file is ready for download as soon as the process completes."
        return {
            "title": title,
            "text": text,
            "primary_text": "Convert now",
            "primary_href": "#converter",
        }

    def _build_internal_links(self, tool_data: dict[str, Any]) -> dict[str, Any]:
        slug = tool_data.get("slug", "")
        if slug == "mp4-to-mp3":
            return {
                "title": "How to convert MP4 to MP3",
                "items": [
                    {
                        "title": "Step-by-step guide",
                        "href": "/blog/how-to-convert-mp4-to-mp3",
                        "description": "Follow the complete walkthrough for converting MP4 files into MP3 audio.",
                    },
                    {
                        "title": "PNG to JPG Converter",
                        "href": "/tools/png-to-jpg",
                        "description": "Try another fast tool for converting image files between common formats.",
                    },
                    {
                        "title": "PDF to Word Converter",
                        "href": "/tools/pdf-to-word",
                        "description": "Convert documents into editable Word files for easier editing.",
                    },
                ],
            }

        return {
            "title": "Related resources",
            "items": [
                {
                    "title": tool_data.get("title", "Converter"),
                    "href": f"/tools/{slug}",
                    "description": "Open the converter page for more details and the upload flow.",
                }
            ],
        }

    def _build_related_converters(self, tool_data: dict[str, Any], related_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if related_tools:
            items = []
            for related in related_tools[:4]:
                slug = related.get("slug") or tool_data.get("slug")
                title = related.get("title") or related.get("slug") or "Converter"
                if isinstance(title, str) and "-" in title:
                    title = title.replace("-", " ").title()
                items.append(
                    {
                        "title": title,
                        "slug": slug,
                        "description": related.get("description") or "Discover another useful conversion flow.",
                        "href": f"/tools/{slug}" if slug else "#",
                    }
                )
            if items:
                return items

        fallback_slug = tool_data.get("slug")
        title = tool_data.get("title") or "Converter"
        return [
            {
                "title": title,
                "slug": fallback_slug,
                "description": tool_data.get("description") or "Discover another useful conversion flow.",
                "href": f"/tools/{fallback_slug}" if fallback_slug else "#",
            }
        ]

    def _build_related_converter(self, tool_data: dict[str, Any], related_converters: list[dict[str, Any]]) -> dict[str, Any]:
        if related_converters:
            related = related_converters[0]
            return {
                "title": related.get("title") or tool_data.get("title", "Converter"),
                "slug": related.get("slug") or tool_data.get("slug"),
                "description": related.get("description") or tool_data.get("description") or "Discover another useful conversion flow.",
                "href": related.get("href") or f"/tools/{tool_data.get('slug')}" if tool_data.get("slug") else "#",
            }
        return {
            "title": tool_data.get("title", "Converter"),
            "slug": tool_data.get("slug"),
            "description": tool_data.get("description") or "Discover another useful conversion flow.",
            "href": f"/tools/{tool_data.get('slug')}" if tool_data.get("slug") else "#",
        }

    def build_context(
        self,
        request: Any,
        tool_data: dict[str, Any],
        faq_items: list[dict[str, str]] | None = None,
        canonical_path: str | None = None,
        meta_overrides: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        seo_data = self.seo_service.build_tool_meta(request, tool_data, canonical_path=canonical_path)
        if meta_overrides:
            seo_data.update(meta_overrides)

        faq = self._prepare_faq(tool_data, faq_items)
        related_tools = self.converter_data_service.resolve_related_tools(tool_data, limit=4)
        related_converters = self._build_related_converters(tool_data, related_tools)
        structured_data = self.seo_service.build_structured_data(
            request,
            tool_data,
            canonical_path=canonical_path,
            page_data={
                "title": seo_data["title"],
                "description": seo_data["description"],
                "url": canonical_path or f"/tools/{tool_data.get('slug', '')}",
                "breadcrumb": self._build_breadcrumb(tool_data, canonical_path),
            },
        )

        landing = {
            "h1": tool_data.get("hero", {}).get("title") or tool_data.get("title", "File Converter"),
            "seo_title": seo_data["title"],
            "meta_description": seo_data["description"],
            "intro": self._build_intro(tool_data),
            "steps": self._build_steps(tool_data),
            "benefits": self._build_benefits(tool_data),
            "supported_formats": self._build_supported_formats(tool_data),
            "tips": self._build_tips(tool_data),
            "common_problems": self._build_common_problems(tool_data),
            "faq": faq,
            "json_ld": structured_data,
            "breadcrumb": self._build_breadcrumb(tool_data, canonical_path),
            "structured_data": structured_data,
            "related_tools": related_tools,
            "related_converters": related_converters,
            "related_converter": self._build_related_converter(tool_data, related_converters),
            "cta": {
                **(tool_data.get("cta") or {}),
                "title": (tool_data.get("cta") or {}).get("title") or f"Convert {tool_data.get('source','file')} files to {tool_data.get('target','output')} in seconds",
                "text": (tool_data.get("cta") or {}).get("text") or "Upload your file and receive a ready-to-use result instantly.",
                "primary_text": (tool_data.get("cta") or {}).get("primary_text") or "Convert now",
                "secondary_text": (tool_data.get("cta") or {}).get("secondary_text") or "Read FAQs",
                "primary_href": (tool_data.get("cta") or {}).get("primary_href") or "#converter",
                "secondary_href": (tool_data.get("cta") or {}).get("secondary_href") or "#faq",
            },
            "download": self._build_download_section(tool_data),
            "internal_links": self._build_internal_links(tool_data),
            "meta": seo_data,
        }
        self.validate_contract(landing)
        return landing
