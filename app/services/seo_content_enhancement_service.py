"""Converigo
SEO Content Enhancement Service
Version : 1.0.0

Reads every converter JSON data file, generates optimized SEO content,
and writes enhanced data back.

Do NOT modify architecture, routing, or converter engine.
Only modifies converter data files (JSON) that feed the template renderer.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.services.converter_registry_service import ConverterRegistryService
from app.services.internal_link_service import InternalLinkService


class SeoContentEnhancementService:
    """Enhance SEO content for all converter landing pages.

    Generates optimized titles, meta descriptions, FAQs, content sections,
    Open Graph tags, and image alt text based on converter metadata.
    """

    # ── Category-specific content templates ──────────────────────

    CATEGORY_META: dict[str, dict[str, str]] = {
        "image": {
            "benefit": "preserve image quality",
            "use_case": "design projects and web publishing",
            "tip": "Always keep the original file as a backup",
            "troubleshoot": "If the output looks different, check your source file dimensions",
        },
        "audio": {
            "benefit": "preserve audio clarity",
            "use_case": "music playback and audio editing",
            "tip": "Choose the right bitrate for your needs",
            "troubleshoot": "If audio quality drops, try a higher bitrate setting",
        },
        "video": {
            "benefit": "maintain video quality",
            "use_case": "video editing and content sharing",
            "tip": "Use compatible codecs for best results",
            "troubleshoot": "If conversion fails, verify the source file is not corrupted",
        },
        "document": {
            "benefit": "preserve document structure",
            "use_case": "professional document workflows",
            "tip": "Review the converted document for layout accuracy",
            "troubleshoot": "Complex formatting may need manual adjustment after conversion",
        },
        "pdf": {
            "benefit": "maintain document integrity",
            "use_case": "document management and archiving",
            "tip": "Check the output for any formatting changes",
            "troubleshoot": "Scanned PDFs may require OCR for text extraction",
        },
        "archive": {
            "benefit": "extract files efficiently",
            "use_case": "file decompression and backup recovery",
            "tip": "Verify extracted files after decompression",
            "troubleshoot": "Password-protected archives require the correct password",
        },
        "general": {
            "benefit": "get reliable results",
            "use_case": "everyday file conversion tasks",
            "tip": "Confirm the output meets your requirements",
            "troubleshoot": "Ensure your file meets the size and format requirements",
        },
    }

    def __init__(self, data_dir: Path | str | None = None) -> None:
        self.data_dir = Path(data_dir or "app/data/converters")
        self.converter_registry = ConverterRegistryService(self.data_dir)
        self.internal_link_service = InternalLinkService(self.data_dir)

    def enhance_all_converters(self) -> dict[str, Any]:
        """Enhance all converter JSON files and return change summary."""
        json_files = sorted(self.data_dir.glob("*.json"))
        enhanced_count = 0
        change_log: list[dict[str, Any]] = []

        for filepath in json_files:
            if filepath.name.endswith(".contract.json") or filepath.name.endswith(".metadata.json"):
                continue

            change = self._enhance_converter_file(filepath)
            if change["modified"]:
                enhanced_count += 1
                change_log.append(change)

        return {
            "total_files_scanned": len([f for f in json_files if not f.name.endswith(".contract.json") and not f.name.endswith(".metadata.json")]),
            "files_enhanced": enhanced_count,
            "changes": change_log,
        }

    def _enhance_converter_file(self, filepath: Path) -> dict[str, Any]:
        """Enhance a single converter JSON file."""
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)

        slug = data.get("slug", filepath.stem)
        category = data.get("category", "general")
        meta = self.CATEGORY_META.get(category, self.CATEGORY_META["general"])
        source = data.get("source", "")
        target = data.get("target", "")
        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""
        title = data.get("title", slug.replace("-", " ").title())
        description = data.get("description", "")

        changes: dict[str, bool] = {}
        original_data = json.dumps(data, ensure_ascii=False, indent=2)

        # ── TASK 1: Title Optimization ──────────────────────────
        title_changed = self._enhance_title(data, slug, source_upper, target_upper)
        changes["title"] = title_changed

        # ── TASK 2: Meta Description ────────────────────────────
        desc_changed = self._enhance_meta_description(data, slug, source_upper, target_upper, description)
        changes["meta_description"] = desc_changed

        # ── TASK 3: FAQ Engine ──────────────────────────────────
        faq_changed = self._enhance_faq(data, slug, source_upper, target_upper, title)
        changes["faq"] = faq_changed

        # ── TASK 4: Content Enhancement ─────────────────────────
        content_changed = self._enhance_content(data, slug, source_upper, target_upper, description, meta)
        changes["content"] = content_changed

        # ── TASK 5: Open Graph ──────────────────────────────────
        og_changed = self._enhance_open_graph(data, slug, source_upper, target_upper)
        changes["open_graph"] = og_changed

        # ── TASK 6: Image Accessibility ─────────────────────────
        alt_changed = self._enhance_image_alt(data, slug, source_upper, target_upper)
        changes["image_alt"] = alt_changed

        modified = any(changes.values())
        if modified:
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")

        return {
            "slug": slug,
            "modified": modified,
            "changes": changes,
        }

    # ── TASK 1: Title Optimization ────────────────────────────────

    def _enhance_title(self, data: dict[str, Any], slug: str, source: str, target: str) -> bool:
        """Generate optimized title (50-60 chars, include Converigo branding)."""
        seo = data.get("seo", {})
        current_title = seo.get("title", "")

        optimized = self._generate_title(slug, source, target)

        if current_title == optimized or (len(current_title) >= 50 and "Converigo" in current_title):
            return False

        if "seo" not in data:
            data["seo"] = {}
        data["seo"]["title"] = optimized
        return True

    def _generate_title(self, slug: str, source: str, target: str) -> str:
        """Generate SEO-optimized title."""
        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""

        # Extract-style converters
        if "extract" in slug.lower():
            fmt = source_upper or slug.replace("-extract", "").upper()
            return f"Extract {fmt} Files Online Free | Converigo"

        # Compress/merge/split converters
        if "compress" in slug.lower():
            fmt = source_upper or ""
            return f"Compress {fmt} Files Online Free | Converigo"
        if "merge" in slug.lower():
            fmt = source_upper or ""
            return f"Merge {fmt} Files Online Free | Converigo"
        if "split" in slug.lower():
            fmt = source_upper or ""
            return f"Split {fmt} Files Online Free | Converigo"

        # Standard conversion
        if source_upper and target_upper:
            return f"Convert {source_upper} to {target_upper} Online Free | Converigo"

        # Fallback
        name = slug.replace("-", " ").title()
        return f"{name} Online Free | Converigo"

    # ── TASK 2: Meta Description ──────────────────────────────────

    def _enhance_meta_description(self, data: dict[str, Any], slug: str, source: str, target: str, description: str) -> bool:
        """Generate optimized meta description (140-160 chars)."""
        seo = data.get("seo", {})
        current_desc = seo.get("description", "")

        optimized = self._generate_meta_description(slug, source, target, description)

        if current_desc == optimized or (140 <= len(current_desc) <= 160):
            return False

        if "seo" not in data:
            data["seo"] = {}
        data["seo"]["description"] = optimized
        return True

    def _generate_meta_description(self, slug: str, source: str, target: str, description: str) -> str:
        """Generate SEO-optimized meta description."""
        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""
        source_lower = source.lower() if source else ""
        target_lower = target.lower() if target else ""

        # Extract converters
        if "extract" in slug.lower():
            fmt_name = source_upper or slug.replace("-extract", "").upper()
            return (
                f"Extract files from {fmt_name} archives online for free using Converigo. "
                f"Fast, secure browser-based {fmt_name} extraction with no software installation required."
            )

        # Compress
        if "compress" in slug.lower():
            return (
                f"Compress {source_lower} files online for free using Converigo. "
                f"Reduce file size while maintaining quality. Fast, secure, browser-based compression."
            )

        # Standard conversion
        if source_upper and target_upper:
            return (
                f"Convert {source_upper} to {target_upper} online for free using Converigo. "
                f"Fast, secure and browser-based file conversion from {source_lower} to {target_lower} "
                f"with no installation required."
            )

        # Fallback
        return (
            f"{description} Fast, secure and browser-based file conversion "
            f"with no installation required. Try Converigo for free today."
        )

    # ── TASK 3: FAQ Engine ────────────────────────────────────────

    def _enhance_faq(self, data: dict[str, Any], slug: str, source: str, target: str, title: str) -> bool:
        """Generate minimum 5 unique FAQ items."""
        existing_faq = data.get("faq", [])
        if not isinstance(existing_faq, list):
            existing_faq = []

        required_count = 5
        if len(existing_faq) >= required_count:
            return False

        # Generate FAQs
        source_lower = source.lower() if source else ""
        target_lower = target.lower() if target else ""
        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""

        standard_faqs = self._generate_standard_faqs(slug, source_upper, target_upper, source_lower, target_lower, title)

        # Combine existing + new, deduplicate by question
        seen_questions: set[str] = set()
        combined: list[dict[str, str]] = []

        for item in existing_faq + standard_faqs:
            q = item.get("question", "").strip().lower()
            if q and q not in seen_questions:
                seen_questions.add(q)
                combined.append(item)

        # Sort: keep existing at top, add new ones after
        existing_questions = {item.get("question", "").strip().lower() for item in existing_faq if item.get("question")}
        ordered: list[dict[str, str]] = list(existing_faq)
        for item in standard_faqs:
            q = item.get("question", "").strip().lower()
            if q and q not in existing_questions:
                ordered.append(item)

        if len(ordered) <= len(existing_faq):
            return False

        data["faq"] = ordered[:10]  # Keep max 10
        return True

    def _generate_standard_faqs(
        self, slug: str, source_upper: str, target_upper: str, source_lower: str, target_lower: str, title: str
    ) -> list[dict[str, str]]:
        """Generate standard FAQ items for any converter."""
        faqs: list[dict[str, str]] = []

        # Q1: Is this free?
        faqs.append({
            "question": f"Is this {source_lower or 'file'} converter free to use?",
            "answer": f"Yes. Converting {source_upper or 'files'} to {target_upper or 'different formats'} on Converigo is completely free with no hidden charges."
        })

        # Q2: Security
        faqs.append({
            "question": "Are my uploaded files secure?",
            "answer": "Yes. All uploaded files are processed securely and automatically deleted from our servers after conversion. Your privacy is protected."
        })

        # Q3: Quality
        faqs.append({
            "question": f"Will the {target_lower or 'output'} quality be preserved?",
            "answer": f"Yes. The converter is designed to produce a high-quality {target_upper or 'output'} file while keeping the conversion process simple and reliable."
        })

        # Q4: Mobile
        faqs.append({
            "question": "Can I use this converter on mobile devices?",
            "answer": "Yes. Converigo works on all modern browsers, including mobile phones and tablets, so you can convert files on the go."
        })

        # Q5: How to
        faqs.append({
            "question": f"How do I convert {source_upper or 'files'} to {target_upper or 'another format'}?",
            "answer": f"Upload your {source_upper or 'file'}, select the conversion options if needed, and download the converted {target_upper or 'result'} instantly. It only takes a few seconds."
        })

        # Q6: File size
        faqs.append({
            "question": "What file sizes are supported?",
            "answer": "We support files up to 100MB for most conversions. Larger files may take longer to process."
        })

        # Q7: CTA
        faqs.append({
            "question": f"Why use Converigo for {source_lower or 'file'} conversion?",
            "answer": f"Converigo offers fast, secure, browser-based {source_lower or 'file'} conversion with no software installation, no registration, and completely free usage."
        })

        return faqs

    # ── TASK 4: Content Enhancement ──────────────────────────────

    def _enhance_content(self, data: dict[str, Any], slug: str, source: str, target: str, description: str, meta: dict[str, str]) -> bool:
        """Enhance content sections with introduction, benefits, how-to, etc."""
        source_lower = source.lower() if source else ""
        target_lower = target.lower() if target else ""
        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""

        # Ensure hero section has enough content
        hero = data.get("hero", {})
        if isinstance(hero, dict):
            current_desc = hero.get("description", "")
            if len(current_desc.split()) < 15:
                hero["description"] = (
                    f"Convert {source_upper} files to {target_upper} online for free. "
                    f"Fast, secure browser-based conversion with no software installation. "
                    f"Get high-quality {target_lower} output in seconds using Converigo."
                )
                data["hero"] = hero

        # Ensure features section has enough items
        features = data.get("features", [])
        if not isinstance(features, list):
            features = []

        # Normalize: some converters have features as list of strings, convert to dicts
        normalized_features: list[dict[str, str]] = []
        for f in features:
            if isinstance(f, str):
                normalized_features.append({"title": f, "text": f})
            elif isinstance(f, dict):
                normalized_features.append(f)
        features = normalized_features

        if len(features) < 5:
            extra_features = [
                {"title": f"Fast {source_lower} to {target_lower} conversion", "text": f"Convert {source_upper} to {target_upper} in seconds with our optimized processing engine."},
                {"title": "No software installation required", "text": "Convert files directly in your browser without downloading or installing any software."},
                {"title": f"High-quality {target_lower} output", "text": f"Receive a polished {target_upper} file ready for immediate use in your workflow."},
                {"title": f"Free {source_lower} to {target_lower} converter", "text": f"Convert {source_upper} to {target_upper} online completely free with no registration or hidden costs."},
                {"title": f"Secure {source_lower} processing", "text": f"Your {source_upper} files are encrypted during upload and automatically deleted after conversion."},
            ]
            seen_titles: set[str] = {f.get("title", "").lower() for f in features if isinstance(f, dict) and f.get("title")}
            for feat in extra_features:
                if feat["title"].lower() not in seen_titles:
                    features.append(feat)
                    seen_titles.add(feat["title"].lower())

            data["features"] = features[:8]

        # Ensure how_to_use section exists and is complete
        how_to = data.get("how_to_use", [])
        if not isinstance(how_to, list):
            how_to = []
        # Normalize how_to: some may be strings
        normalized_howto: list[dict[str, str]] = []
        for h in how_to:
            if isinstance(h, str):
                normalized_howto.append({"title": h, "description": h})
            elif isinstance(h, dict):
                normalized_howto.append(h)
        how_to = normalized_howto
        if len(how_to) < 4:
            extra_steps = [
                {"title": f"Upload your {source_lower or 'file'}", "description": f"Select a {source_upper or ''} file from your device to begin the conversion process."},
                {"title": f"Choose {target_lower or 'output'} as format", "description": f"Pick {target_upper or 'the output'} as your desired format and review any available options."},
                {"title": f"Convert {source_lower} to {target_lower}", "description": f"Click convert and our engine processes your {source_lower or 'file'} instantly."},
                {"title": f"Download your {target_lower or 'converted'} file", "description": f"Get your converted {target_upper or 'file'} immediately for use in your projects."},
            ]
            seen_howto: set[str] = {h.get("title", "").lower() for h in how_to if isinstance(h, dict) and h.get("title")}
            for step in extra_steps:
                if step["title"].lower() not in seen_howto:
                    how_to.append(step)
                    seen_howto.add(step["title"].lower())
            data["how_to_use"] = how_to[:6]

        # Ensure about_formats section exists with details
        about = data.get("about_formats", [])
        if not isinstance(about, list):
            about = []
        # Normalize about_formats
        normalized_about: list[dict[str, str]] = []
        for a in about:
            if isinstance(a, str):
                normalized_about.append({"title": a, "text": a})
            elif isinstance(a, dict):
                normalized_about.append(a)
        about = normalized_about
        if len(about) < 3:
            extra_about = [
                {"title": f"What is {source_upper or 'the input'} format?", "text": f"{source_upper or 'The input'} is a widely used file format known for its versatility and compatibility across many applications."} if source_upper else None,
                {"title": f"What is {target_upper or 'the output'} format?", "text": f"{target_upper or 'The output'} is a popular file format chosen for its broad compatibility and optimized performance."} if target_upper else None,
                {"title": f"Why convert {source_upper or 'formats'} to {target_upper or 'another'}?", "text": f"Converting {source_lower or 'files'} to {target_lower or 'another format'} enables better compatibility, smaller file sizes, and improved workflow integration."} if source_upper and target_upper else None,
            ]
            extra_about = [a for a in extra_about if a is not None]
            seen_about: set[str] = {a.get("title", "").lower() for a in about if isinstance(a, dict) and a.get("title")}
            for a in extra_about:
                if a["title"].lower() not in seen_about:
                    about.append(a)
                    seen_about.add(a["title"].lower())
            data["about_formats"] = about[:4]

        return True

    # ── TASK 5: Open Graph ────────────────────────────────────────

    def _enhance_open_graph(self, data: dict[str, Any], slug: str, source: str, target: str) -> bool:
        """Ensure Open Graph tags are complete."""
        seo = data.get("seo", {})
        if not isinstance(seo, dict):
            seo = {}
            data["seo"] = seo

        source_lower = source.lower() if source else ""
        target_lower = target.lower() if target else ""
        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""

        title = seo.get("title", "")
        description = seo.get("description", "")
        keywords = seo.get("keywords", "")

        # Ensure OG fields in seo section
        current_og_image = seo.get("image", "")
        if not current_og_image:
            seo["image"] = "/static/images/og-default.png"

        current_og_image_alt = seo.get("og_image_alt", "")
        if not current_og_image_alt:
            if source_upper and target_upper:
                seo["og_image_alt"] = f"Convert {source_upper} to {target_upper} - Converigo free online converter"
            else:
                seo["og_image_alt"] = "Converigo free online file converter"

        # Also add twitter fields to seo
        current_twitter_title = seo.get("twitter_title", "")
        if not current_twitter_title:
            seo["twitter_title"] = title or f"Convert {source_upper or ''} to {target_upper or ''} | Converigo"

        current_twitter_desc = seo.get("twitter_description", "")
        if not current_twitter_desc:
            seo["twitter_description"] = description or f"Convert {source_upper} to {target_upper} online for free at Converigo."

        current_twitter_image = seo.get("twitter_image", "")
        if not current_twitter_image:
            seo["twitter_image"] = seo.get("image", "/static/images/og-default.png")

        # Ensure keywords exist
        if not keywords or len(keywords.split(",")) < 3:
            if source_lower and target_lower:
                seo["keywords"] = f"{source_lower} to {target_lower}, convert {source_lower} to {target_lower}, {source_lower} converter, {target_lower} converter, online file converter"
            else:
                seo["keywords"] = f"{slug.replace('-', ' ')}, online converter, file conversion, free converter, Converigo"

        return True

    # ── TASK 6: Image Accessibility ───────────────────────────────

    def _enhance_image_alt(self, data: dict[str, Any], slug: str, source: str, target: str) -> bool:
        """Add image alt text for accessibility."""
        seo = data.get("seo", {})
        if not isinstance(seo, dict):
            seo = {}
            data["seo"] = seo

        source_upper = source.upper() if source else ""
        target_upper = target.upper() if target else ""

        current_alt = seo.get("og_image_alt", "")
        if current_alt:
            return False

        if source_upper and target_upper:
            seo["og_image_alt"] = f"Convert {source_upper} to {target_upper} online free with Converigo converter tool"
        else:
            name = slug.replace("-", " ").title()
            seo["og_image_alt"] = f"{name} - Converigo free online file converter tool"

        return True

