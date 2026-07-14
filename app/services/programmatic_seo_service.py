from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.registry import ConverterRegistry, registry
from app.services.converter_registry_service import ConverterRegistryService


class ProgrammaticSEOService:
    """Generate deterministic SEO payloads from converter contracts."""

    def __init__(
        self,
        contracts_dir: Path | str,
        registry_instance: ConverterRegistry | None = None,
    ) -> None:
        self.contracts_dir = Path(contracts_dir)
        self.registry = registry_instance or registry
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)

    def generate_all(self) -> dict[str, dict[str, Any]]:
        payloads: dict[str, dict[str, Any]] = {}
        for contract in self.converter_registry_service.get_active():
            slug = str(contract.get("slug", "")).strip()
            if not slug:
                continue
            if not self._is_registered(slug):
                continue
            payloads[slug] = self.generate_payload(contract)
        return dict(sorted(payloads.items(), key=lambda item: item[0]))

    def generate_payload(self, contract: dict[str, Any]) -> dict[str, Any]:
        slug = str(contract.get("slug", "")).strip()
        name = str(contract.get("name", slug or "Converter")).strip()
        category = str(contract.get("category", "general")).strip().lower()
        description = str(contract.get("description", "")).strip()
        canonical_url = str(contract.get("canonical_url", "")).strip()
        source_formats = [str(entry) for entry in contract.get("input_formats", [])]
        target_formats = [str(entry) for entry in contract.get("output_formats", [])]
        source_label = ", ".join(source_formats).upper() or "FILE"
        target_label = ", ".join(target_formats).upper() or "OUTPUT"

        seo_title = self._template_substitute(
            "{name} | Converigo",
            {"name": name, "category": category, "slug": slug},
        )
        meta_description = self._template_substitute(
            "Convert {source} files to {target} online free and securely.",
            {
                "source": source_label,
                "target": target_label,
                "name": name,
                "category": category,
                "slug": slug,
                "description": description,
            },
        )
        intro = {
            "title": self._template_substitute("How to convert {source} to {target}", {"source": source_label, "target": target_label}),
            "text": self._template_substitute(
                "Use this tool to convert {source} files into {target} output in seconds.",
                {"source": source_label, "target": target_label, "description": description},
            ),
        }
        steps = [
            {
                "title": "Upload your file",
                "description": self._template_substitute("Select a {source} file from your device to start the conversion.", {"source": source_label}),
            },
            {
                "title": "Choose the output format",
                "description": self._template_substitute("Pick {target} as the result format and review the conversion options.", {"target": target_label}),
            },
            {
                "title": "Download the converted file",
                "description": "Get the finished result instantly, ready to share or keep in your workflow.",
            },
        ]
        benefits = [
            {
                "title": "Fast conversion",
                "text": self._template_substitute("Convert {source} files to {target} quickly and securely.", {"source": source_label, "target": target_label}),
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
        supported_formats = {
            "input": [source_label],
            "output": [target_label],
            "description": self._template_substitute("{source} input, {target} output", {"source": source_label, "target": target_label}),
        }
        tips = [
            {
                "title": "Keep a backup",
                "text": self._template_substitute("Save your original {source} file before you begin a conversion.", {"source": source_label}),
            },
            {
                "title": "Choose the right preset",
                "text": self._template_substitute("Select a {target} preset that matches your downstream workflow.", {"target": target_label}),
            },
            {
                "title": "Check the result",
                "text": "Open the downloaded file to confirm that the conversion looks correct.",
            },
        ]
        common_problems = [
            {
                "title": "File not accepted",
                "text": self._template_substitute("Use a supported {source} file and confirm the upload size before trying again.", {"source": source_label}),
            },
            {
                "title": "Output looks different than expected",
                "text": self._template_substitute("Try a different {target} preset or re-upload the source file if the result is incomplete.", {"target": target_label}),
            },
            {
                "title": "Conversion is slow",
                "text": "Large files can take a little longer, but the process should finish without extra steps.",
            },
        ]
        faq = [
            {
                "question": self._template_substitute("What is {name} conversion?", {"name": name}),
                "answer": self._template_substitute("Use {name} to convert your files quickly and securely.", {"name": name}),
            },
            {
                "question": self._template_substitute("How do I convert {source} to {target}?", {"source": source_label, "target": target_label}),
                "answer": "Upload your file, choose the output format, and download the converted result.",
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
            {
                "question": "Is this converter free to use?",
                "answer": "Yes, this converter is free for standard conversion tasks.",
            },
        ]
        cta = {
            "title": self._template_substitute("Convert {source} to {target}", {"source": source_label, "target": target_label}),
            "text": self._template_substitute("Convert your {source} files to {target} in seconds.", {"source": source_label, "target": target_label}),
        }
        related_keywords = [
            f"{name.lower()} converter",
            f"{category} conversion",
            f"{source_label.lower()} to {target_label.lower()}",
            f"{slug} online",
        ]
        related_converters = [
            {
                "slug": slug,
                "title": name,
                "description": description or f"Convert {source_label} files to {target_label} online.",
            }
        ]
        breadcrumb = [
            {"name": "Home", "url": "/"},
            {"name": name, "url": canonical_url or f"/{slug}"},
        ]
        json_ld = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": seo_title,
            "description": meta_description,
            "url": canonical_url or f"/{slug}",
            "breadcrumb": breadcrumb,
        }

        return {
            "slug": slug,
            "seo_title": seo_title,
            "meta_description": meta_description,
            "intro": intro,
            "steps": steps,
            "benefits": benefits,
            "supported_formats": supported_formats,
            "tips": tips,
            "common_problems": common_problems,
            "faq": faq,
            "cta": cta,
            "related_keywords": related_keywords,
            "related_converters": related_converters,
            "breadcrumb": breadcrumb,
            "json_ld": json_ld,
            "canonical_url": canonical_url or f"https://converigo.com/{slug}",
        }

    def _template_substitute(self, text: str, values: dict[str, Any]) -> str:
        result = text
        for key, value in sorted(values.items()):
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _is_registered(self, slug: str) -> bool:
        return self.registry.get(slug) is not None or self.registry.get(slug.replace("-", "_")) is not None
