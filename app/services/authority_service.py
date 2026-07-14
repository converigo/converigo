from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from app.services.converter_registry_service import ConverterRegistryService


class AuthorityService:
    """Generate deterministic authority payloads for file formats."""

    REQUIRED_SECTIONS = [
        "history",
        "specification",
        "developer_maintainer",
        "mime_type",
        "file_extension",
        "category",
        "compression",
        "encoding",
        "metadata",
        "typical_file_size",
        "compatibility",
        "operating_system_support",
        "software_support",
        "advantages",
        "disadvantages",
        "security_considerations",
        "accessibility",
        "performance",
        "common_problems",
        "troubleshooting",
        "alternatives",
        "comparison",
        "best_practices",
        "glossary",
        "related_formats",
        "references",
    ]

    HUB_SLUG_BY_CATEGORY = {
        "video": "video-converter",
        "image": "image-converter",
        "pdf": "pdf-tools",
        "document": "pdf-tools",
        "audio": "audio-tools",
        "archive": "archive-tools",
    }

    MIME_TYPE_BY_FORMAT = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "svg": "image/svg+xml",
        "tiff": "image/tiff",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
        "mkv": "video/x-matroska",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "aac": "audio/aac",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "zip": "application/zip",
        "rar": "application/vnd.rar",
        "tar": "application/x-tar",
        "7z": "application/x-7z-compressed",
        "txt": "text/plain",
        "rtf": "application/rtf",
        "odt": "application/vnd.oasis.opendocument.text",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
    }

    CATEGORY_BY_FORMAT = {
        "mp4": "video",
        "mov": "video",
        "avi": "video",
        "mkv": "video",
        "webm": "video",
        "mp3": "audio",
        "wav": "audio",
        "flac": "audio",
        "aac": "audio",
        "m4a": "audio",
        "ogg": "audio",
        "jpg": "image",
        "jpeg": "image",
        "png": "image",
        "gif": "image",
        "webp": "image",
        "bmp": "image",
        "svg": "image",
        "tiff": "image",
        "pdf": "document",
        "doc": "document",
        "docx": "document",
        "ppt": "document",
        "pptx": "document",
        "xls": "document",
        "xlsx": "document",
        "txt": "document",
        "rtf": "document",
        "odt": "document",
        "ods": "document",
        "zip": "archive",
        "rar": "archive",
        "tar": "archive",
        "7z": "archive",
        "gz": "archive",
    }

    SOFTWARE_SUPPORT_BY_CATEGORY = {
        "document": ["Microsoft Office", "LibreOffice", "Google Workspace", "Adobe Acrobat"],
        "image": ["Adobe Photoshop", "GIMP", "Affinity Photo", "Preview"],
        "video": ["VLC", "Adobe Premiere", "DaVinci Resolve", "FFmpeg"],
        "audio": ["Audacity", "Apple Music", "VLC", "Adobe Audition"],
        "archive": ["7-Zip", "WinRAR", "WinZip", "macOS Archive Utility"],
        "general": ["Cross-platform applications", "Browser-based tools", "Command line utilities"],
    }

    OPERATING_SYSTEM_SUPPORT = ["Windows", "macOS", "Linux", "iOS", "Android"]

    def __init__(self, contracts_dir: Path | str) -> None:
        self.registry = ConverterRegistryService(contracts_dir)

    def generate_all(self) -> dict[str, dict[str, Any]]:
        formats = sorted(self._collect_formats())
        return {format_name: self.generate_payload(format_name) for format_name in formats}

    def generate_payload(self, format_name: str) -> dict[str, Any]:
        normalized = self._normalize_format(format_name)
        label = normalized.upper()
        category = self._infer_category(normalized)
        mime_type = self.MIME_TYPE_BY_FORMAT.get(normalized, "application/octet-stream")
        hub_reference = self._build_hub_reference(category)

        canonical_url = f"https://converigo.com/{normalized}"
        payload = {
            "slug": normalized,
            "title": f"{label} File Format",
            "description": self._build_description(normalized, category),
            "category": category,
            "source": normalized,
            "target": normalized,
            "landing_path": f"/{normalized}",
            "canonical_url": canonical_url,
            "hero": {"title": f"{label} Authority Hub"},
            "seo": {
                "title": f"{label} Authority Hub | Converigo",
                "description": self._build_description(normalized, category),
                "canonical": canonical_url,
            },
            "supported_formats": {
                "input": [label],
                "output": [label],
                "description": f"{label} file support for authoring, viewing, and conversion.",
            },
            "cta": {
                "title": f"Explore {label} format resources",
                "text": f"Learn how {label} files work and which tools support them.",
                "primary_text": "Open format hub",
                "primary_href": hub_reference["href"],
                "secondary_text": "View related tools",
                "secondary_href": f"/{hub_reference['href'].lstrip('/')}",
            },
            "faq": self._build_faq(label, category),
            "related_tools": self._build_related_formats(normalized, category),
            "related_formats": self._build_related_formats(normalized, category),
            "related_converters": self._build_related_formats(normalized, category),
            "internal_links": self._build_internal_links(normalized, category, hub_reference),
            "history": self._build_history(label, category),
            "specification": self._build_specification(label, category),
            "developer_maintainer": self._build_developer_maintainer(label, category),
            "mime_type": mime_type,
            "file_extension": f".{normalized}",
            "compression": self._build_compression(normalized, category),
            "encoding": self._build_encoding(normalized, category),
            "metadata": self._build_metadata(normalized, category),
            "typical_file_size": self._build_typical_file_size(category),
            "compatibility": self._build_compatibility(normalized, category),
            "operating_system_support": ", ".join(self.OPERATING_SYSTEM_SUPPORT),
            "software_support": self._build_software_support(category),
            "advantages": self._build_advantages(label, category),
            "disadvantages": self._build_disadvantages(label, category),
            "security_considerations": self._build_security_considerations(label, category),
            "accessibility": self._build_accessibility(label, category),
            "performance": self._build_performance(label, category),
            "common_problems": self._build_common_problems(label, category),
            "troubleshooting": self._build_troubleshooting(label, category),
            "alternatives": self._build_alternatives(label, category),
            "comparison": self._build_comparison(label, category),
            "best_practices": self._build_best_practices(label, category),
            "glossary": self._build_glossary(label, category),
            "references": self._build_references(label, category),
        }

        self.validate_payload(payload)
        return payload

    def validate_payload(self, payload: dict[str, Any]) -> None:
        missing = []
        for section in sorted(self.REQUIRED_SECTIONS):
            value = payload.get(section)
            if section in {
                "history",
                "specification",
                "developer_maintainer",
                "mime_type",
                "file_extension",
                "category",
                "compression",
                "encoding",
                "metadata",
                "typical_file_size",
                "compatibility",
                "operating_system_support",
            }:
                if not isinstance(value, str) or not value.strip():
                    missing.append(section)
            elif section == "software_support":
                if not isinstance(value, list) or not value:
                    missing.append(section)
            elif section in {
                "advantages",
                "disadvantages",
                "security_considerations",
                "accessibility",
                "performance",
                "common_problems",
                "troubleshooting",
                "alternatives",
                "comparison",
                "best_practices",
                "glossary",
                "related_formats",
            }:
                if not isinstance(value, list) or not value:
                    missing.append(section)
            elif section == "references":
                if not isinstance(value, list) or not value:
                    missing.append(section)
            else:
                if not value:
                    missing.append(section)
        if missing:
            raise ValueError(f"Authority payload missing required sections: {', '.join(missing)}")

    def _collect_formats(self) -> set[str]:
        formats: list[str] = []
        for contract in self.registry.get_active():
            formats.extend(str(item).strip().lower() for item in contract.get("input_formats", []) if str(item).strip())
            formats.extend(str(item).strip().lower() for item in contract.get("output_formats", []) if str(item).strip())
        return {fmt for fmt in formats if fmt}

    def _normalize_format(self, format_name: str) -> str:
        return str(format_name or "").strip().lower()

    def _infer_category(self, format_name: str) -> str:
        if format_name in self.CATEGORY_BY_FORMAT:
            return self.CATEGORY_BY_FORMAT[format_name]

        categories = Counter()
        for contract in self.registry.get_active():
            formats = [str(item).strip().lower() for item in contract.get("input_formats", []) + contract.get("output_formats", [])]
            if format_name in formats:
                categories[str(contract.get("category", "general")).strip().lower()] += 1
        return categories.most_common(1)[0][0] if categories else "general"

    def _build_description(self, format_name: str, category: str) -> str:
        return f"{format_name.upper()} is a widely used {category} file format with broad support across tools and platforms."

    def _build_history(self, format_name: str, category: str) -> str:
        history_map = {
            "pdf": "Created by Adobe in 1993, PDF was designed to preserve fixed-layout documents across devices.",
            "docx": "Created as part of Microsoft Office Open XML in 2007 to replace the older DOC format.",
            "mp4": "Standardized by the Moving Picture Experts Group (MPEG) in 2001 as a versatile video container.",
            "mp3": "Standardized in the early 1990s, MP3 became the dominant digital audio format for music distribution.",
            "png": "Developed by the W3C in 1996 as a patent-free successor to GIF for lossless images.",
            "jpg": "Created by the Joint Photographic Experts Group in 1992 for efficient photographic image storage.",
            "zip": "Invented in 1989, ZIP became the most popular archive format for compressed files.",
            "rar": "Developed in 1993 by Eugene Roshal, RAR is a proprietary archive format with strong compression.",
        }
        return history_map.get(format_name, f"{format_name.upper()} has a long history as a practical file format in its category.")

    def _build_specification(self, format_name: str, category: str) -> str:
        return f"{format_name.upper()} is defined by an established file specification and is widely documented by the format community."

    def _build_developer_maintainer(self, format_name: str, category: str) -> str:
        return (
            f"{format_name.upper()} is maintained through its standardization body and broad ecosystem support. "
            "Open formats are often improved by community contributors and software vendors."
        )

    def _build_compression(self, format_name: str, category: str) -> str:
        compression_map = {
            "pdf": "PDF content may use lossless compression for text and images, and optional JPEG compression for embedded images.",
            "docx": "DOCX packages are ZIP archives containing XML, so compression depends on the container and internal file contents.",
            "jpg": "JPG uses lossy compression, optimizing photographic images by discarding some visual detail.",
            "png": "PNG uses lossless compression, preserving exact image data with algorithms like DEFLATE.",
            "mp4": "MP4 containers hold compressed audio/video streams, such as H.264 video and AAC audio.",
            "mp3": "MP3 uses lossy audio compression designed for efficient storage and streaming.",
            "zip": "ZIP archives compress contained files with a range of algorithms, often using DEFLATE.",
            "rar": "RAR archives support efficient compression and multi-volume archives with optional encryption.",
        }
        return compression_map.get(format_name, "Compression behavior varies by file content and encoder settings.")

    def _build_encoding(self, format_name: str, category: str) -> str:
        encoding_map = {
            "pdf": "PDF uses structured objects and streams with optional text encodings like UTF-8.",
            "docx": "DOCX stores document data in XML files inside a ZIP archive, using character encodings like UTF-8.",
            "jpg": "JPG encodes image data using discrete cosine transform (DCT) and quantization.",
            "png": "PNG encodes images with lossless filtering and compression based on DEFLATE.",
            "mp4": "MP4 uses container-level metadata with compressed audio and video tracks encoded by codecs.",
            "mp3": "MP3 encodes audio in frames using perceptual compression and bitrate scaling.",
        }
        return encoding_map.get(format_name, "Encoding depends on the format family and standard codec definitions.")

    def _build_metadata(self, format_name: str, category: str) -> str:
        metadata_map = {
            "pdf": "PDF supports metadata in XMP, document information dictionaries, and embedded object metadata.",
            "docx": "DOCX supports metadata via embedded XML properties and custom document properties.",
            "jpg": "JPG often carries metadata in EXIF, IPTC, and XMP blocks.",
            "png": "PNG supports metadata chunks such as tEXt, iTXt, and zTXt.",
            "mp4": "MP4 files can include metadata tracks and tags for title, author, and media information.",
            "mp3": "MP3 commonly stores metadata in ID3 tags for artist, album, and track information.",
            "zip": "ZIP archives do not standardize metadata beyond file names, timestamps, and optional extra fields.",
        }
        return metadata_map.get(format_name, "This format carries metadata in its standard container or file headers.")

    def _build_typical_file_size(self, category: str) -> str:
        size_map = {
            "document": "Typical sizes range from a few kilobytes for text-heavy documents to several megabytes for rich content.",
            "image": "Image files usually range from tens of kilobytes to several megabytes depending on resolution and compression.",
            "video": "Video files often range from megabytes to gigabytes, depending on duration and codec quality.",
            "audio": "Audio files commonly range from a few megabytes for short clips to tens of megabytes for high-quality tracks.",
            "archive": "Archive sizes vary widely based on contained files, but compressed archives often shrink data by 20-70%.",
        }
        return size_map.get(category, "File size varies by content, resolution, and compression settings.")

    def _build_compatibility(self, format_name: str, category: str) -> str:
        return f"{format_name.upper()} is widely compatible with modern desktop, mobile, and web tools within its category."

    def _build_software_support(self, category: str) -> list[dict[str, str]]:
        examples = self.SOFTWARE_SUPPORT_BY_CATEGORY.get(category, self.SOFTWARE_SUPPORT_BY_CATEGORY["general"])
        return [{"title": software, "text": f"Supports {software} for {category} file workflows."} for software in examples]

    def _build_advantages(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Wide support", "text": f"{format_name.upper()} is supported by many applications and services."},
            {"title": "Interoperability", "text": "The format is recognized across platforms and workflow tools."},
        ]

    def _build_disadvantages(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "File size", "text": "Some formats can produce large files depending on quality settings."},
            {"title": "Format complexity", "text": "Advanced features may not be supported by every tool."},
        ]

    def _build_security_considerations(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Malicious content", "text": "Verify files from unknown sources before opening them."},
            {"title": "Embedded scripts", "text": "Some formats can carry active content or macros that should be handled carefully."},
        ]

    def _build_accessibility(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Text alternatives", "text": "Provide text descriptions for images, audio transcripts, and captions where possible."},
            {"title": "Platform support", "text": "Choose tools that support accessibility features for this file format."},
        ]

    def _build_performance(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Load performance", "text": "Smaller files open faster and are easier to transfer."},
            {"title": "Processing time", "text": "Conversion speed depends on format complexity and file size."},
        ]

    def _build_common_problems(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Unsupported format", "text": "Make sure the file extension matches the expected format."},
            {"title": "Corrupt files", "text": "A damaged file may fail to open or convert correctly."},
        ]

    def _build_troubleshooting(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Check the extension", "text": "Confirm the file uses the correct extension and file header."},
            {"title": "Try a different tool", "text": "Use another application if the current tool cannot open the file."},
        ]

    def _build_alternatives(self, format_name: str, category: str) -> list[dict[str, str]]:
        alternatives = {
            "pdf": ["DOCX", "HTML"],
            "docx": ["PDF", "ODT"],
            "mp4": ["MOV", "WEBM"],
            "mp3": ["WAV", "AAC"],
            "png": ["JPG", "WEBP"],
            "jpg": ["PNG", "WEBP"],
            "zip": ["RAR", "TAR"],
            "rar": ["ZIP", "7Z"],
        }
        options = alternatives.get(format_name, [])
        if not options:
            options = [format_name.upper()]
        return [{"title": option, "text": f"A possible alternative for similar use cases is {option}."} for option in options]

    def _build_comparison(self, format_name: str, category: str) -> list[dict[str, str]]:
        comparisons = {
            "pdf": ["Compare PDF to DOCX for fixed-layout vs editable documents."],
            "docx": ["Compare DOCX to PDF for editability versus portability."],
            "mp4": ["Compare MP4 to WEBM for web playback compatibility."],
            "mp3": ["Compare MP3 to WAV for compressed versus uncompressed audio."],
            "png": ["Compare PNG to JPG for lossless versus lossy image workflows."],
            "jpg": ["Compare JPG to PNG for photographic images versus graphics."],
            "zip": ["Compare ZIP to RAR for archive compatibility versus compression ratio."],
        }
        items = comparisons.get(format_name, [f"Compare {format_name.upper()} to other formats in the same category for the best workflow."])
        return [{"title": "Format comparison", "text": item} for item in items]

    def _build_best_practices(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "Keep originals", "text": "Save a copy of the original file before converting or editing."},
            {"title": "Use compatible tools", "text": "Choose software that explicitly supports the format for best results."},
        ]

    def _build_glossary(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"term": format_name.upper(), "definition": f"The {format_name.upper()} file format."},
            {"term": "MIME type", "definition": "A standardized identifier used to describe the file content type."},
        ]

    def _build_references(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"title": "IANA Media Types", "url": "https://www.iana.org/assignments/media-types/media-types.xhtml", "type": "specification"},
            {"title": "File format guidance", "url": "https://en.wikipedia.org/wiki/Computer_file_format", "type": "reference"},
        ]

    def _build_faq(self, format_name: str, category: str) -> list[dict[str, str]]:
        return [
            {"question": f"What is {format_name.upper()}?", "answer": f"{format_name.upper()} is a file format used in {category} workflows."},
            {"question": "Which applications support it?", "answer": "Most modern applications in the category support this format."},
            {"question": "Is it portable?", "answer": "Yes, it is designed for cross-platform use and broad compatibility."},
            {"question": "Can it be converted?", "answer": "Yes, many tools can convert it to other related file formats."},
            {"question": "How do I open it?", "answer": "Use a compatible viewer or editor for the format."},
            {"question": "Is metadata preserved?", "answer": "Metadata handling depends on the format and the tool used."},
        ]

    def _build_related_formats(self, format_name: str, category: str) -> list[dict[str, str]]:
        formats = sorted({
            fmt
            for contract in self.registry.get_active()
            for fmt in [str(item).strip().lower() for item in contract.get("input_formats", []) + contract.get("output_formats", [])]
            if fmt and fmt != format_name and self._infer_category(fmt) == category
        })
        related = [
            {
                "slug": candidate,
                "title": f"{candidate.upper()} format",
                "description": f"Learn about {candidate.upper()} files and how they compare to {format_name.upper()}",
                "href": f"/{candidate}",
            }
            for candidate in formats[:4]
        ]
        if not related:
            related.append(
                {
                    "slug": category,
                    "title": f"{category.title()} tools",
                    "description": f"Explore other tools and formats in the {category} category.",
                    "href": self._build_hub_reference(category)["href"],
                }
            )
        return related

    def _build_internal_links(self, format_name: str, category: str, hub_reference: dict[str, str]) -> dict[str, Any]:
        return {
            "title": "Related resources",
            "items": [
                {
                    "title": f"Open the {format_name.upper()} authority hub",
                    "href": f"/{format_name}",
                    "description": "Explore format authority content and related tools.",
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
        title = {
            "video-converter": "Video Conversion Hub",
            "image-converter": "Image Conversion Hub",
            "pdf-tools": "PDF Tools Hub",
            "audio-tools": "Audio Tools Hub",
            "archive-tools": "Archive Tools Hub",
        }.get(hub_slug, "Conversion Hub")
        description = {
            "video-converter": "Convert videos into the formats you need for sharing, editing, and playback.",
            "image-converter": "Convert images for web use, editing, compatibility, and sharing.",
            "pdf-tools": "Work with PDFs and related document conversion flows in one hub.",
            "audio-tools": "Convert and manage audio files for playback, editing, and sharing.",
            "archive-tools": "Extract, merge, and compress archive files with fast browser-based tools.",
        }.get(hub_slug, "Explore related conversion tools in the hub.")
        href = f"/{hub_slug}"
        return {"title": title, "href": href, "description": description}
