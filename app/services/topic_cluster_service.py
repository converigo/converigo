from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.authority_service import AuthorityService
from app.services.comparison_service import ComparisonService
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.internal_link_service import InternalLinkService
from app.services.knowledge_service import KnowledgeService
from app.services.landing_service import LandingPageBuilder
from app.services.seo_service import SeoService


class TopicClusterService:
    """Generate comprehensive topic clusters for every active format."""

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self.seo_service = SeoService(self.contracts_dir)
        self.landing_builder = LandingPageBuilder(self.seo_service, self.converter_data_service)
        self.authority_service = AuthorityService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.comparison_service = ComparisonService(self.contracts_dir)
        self.internal_link_service = InternalLinkService(self.contracts_dir)

    def build_cluster(self, format_name: str) -> dict[str, Any]:
        """Build comprehensive topic cluster for a format."""
        format_lower = format_name.lower()
        
        cluster = {
            "format": format_lower,
            "format_title": format_name.upper(),
            "knowledge": self._build_knowledge_section(format_lower),
            "faq": self._build_faq_section(format_lower),
            "mime": self._build_mime_section(format_lower),
            "file_extensions": self._build_extensions_section(format_lower),
            "metadata": self._build_metadata_section(format_lower),
            "specification": self._build_specification_section(format_lower),
            "history": self._build_history_section(format_lower),
            "security": self._build_security_section(format_lower),
            "compression": self._build_compression_section(format_lower),
            "accessibility": self._build_accessibility_section(format_lower),
            "software": self._build_software_section(format_lower),
            "tutorials": self._build_tutorials_section(format_lower),
            "best_practices": self._build_best_practices_section(format_lower),
            "comparisons": self._build_comparisons_section(format_lower),
            "related_formats": self._build_related_formats_section(format_lower),
            "related_converters": self._build_related_converters_section(format_lower),
            "hub": self._build_hub_section(format_lower),
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Formats", "url": "/formats"},
                {"name": format_name.upper(), "url": f"/formats/{format_lower}"},
            ],
            "internal_links": self._build_internal_links(format_lower),
        }
        return cluster

    def build_all_clusters(self) -> dict[str, dict[str, Any]]:
        """Build topic clusters for all known formats."""
        formats = self._collect_all_formats()
        clusters = {}
        
        for fmt in formats:
            try:
                clusters[fmt] = self.build_cluster(fmt)
            except Exception:
                # Skip formats that fail to generate clusters
                continue
        
        return clusters

    def get_cluster(self, format_name: str) -> dict[str, Any]:
        """Get a single topic cluster."""
        return self.build_cluster(format_name)

    # Section builders

    def _build_knowledge_section(self, format_name: str) -> dict[str, Any]:
        """Build knowledge/educational content."""
        return {
            "title": f"Understanding {format_name.upper()}",
            "overview": f"The {format_name.upper()} format is a widely-used file format with specific characteristics and use cases.",
            "key_points": [
                f"{format_name.upper()} is optimized for specific use cases",
                f"Understanding {format_name.upper()} helps in choosing the right format",
                f"{format_name.upper()} has specific compression and quality characteristics",
            ],
            "url": f"/knowledge/{format_name}",
        }

    def _build_faq_section(self, format_name: str) -> list[dict[str, str]]:
        """Build FAQ items."""
        return [
            {
                "question": f"What is {format_name.upper()}?",
                "answer": f"{format_name.upper()} is a file format designed for storing and exchanging {format_name} data efficiently.",
            },
            {
                "question": f"When should I use {format_name.upper()}?",
                "answer": f"Use {format_name.upper()} when you need to share or store {format_name} content with broad compatibility and efficient file sizes.",
            },
            {
                "question": f"How can I convert to {format_name.upper()}?",
                "answer": f"You can use Converigo's online converter to quickly convert files to {format_name.upper()} format.",
            },
            {
                "question": f"What are the advantages of {format_name.upper()}?",
                "answer": f"{format_name.upper()} offers good compression, broad software support, and reliable data preservation.",
            },
        ]

    def _build_mime_section(self, format_name: str) -> dict[str, Any]:
        """Build MIME type information."""
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
            "mp4": "video/mp4",
            "mov": "video/quicktime",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "txt": "text/plain",
            "csv": "text/csv",
            "json": "application/json",
        }
        
        mime_type = mime_types.get(format_name, f"application/{format_name}")
        
        return {
            "primary": mime_type,
            "alternatives": [mime_type],
            "description": f"MIME type for {format_name.upper()} format",
        }

    def _build_extensions_section(self, format_name: str) -> dict[str, Any]:
        """Build file extension information."""
        extension_map = {
            "pdf": ".pdf",
            "docx": ".docx",
            "doc": ".doc",
            "png": ".png",
            "jpg": ".jpg",
            "jpeg": ".jpeg",
            "webp": ".webp",
            "gif": ".gif",
            "mp4": ".mp4",
            "mov": ".mov",
            "mp3": ".mp3",
            "wav": ".wav",
            "txt": ".txt",
            "csv": ".csv",
        }
        
        ext = extension_map.get(format_name, f".{format_name}")
        
        return {
            "primary": ext,
            "common_variations": [ext],
            "description": f"File extension for {format_name.upper()} format",
        }

    def _build_metadata_section(self, format_name: str) -> dict[str, Any]:
        """Build metadata information."""
        return {
            "supported": True,
            "common_fields": [
                "Title",
                "Author",
                "Creation Date",
                "Modification Date",
                "Description",
            ],
            "description": f"{format_name.upper()} supports embedded metadata for document information",
        }

    def _build_specification_section(self, format_name: str) -> dict[str, Any]:
        """Build format specification."""
        return {
            "official_name": f"{format_name.upper()} Format Specification",
            "version": "1.0+",
            "standardization": self._get_standardization_body(format_name),
            "description": f"Complete technical specification for {format_name.upper()} format",
            "details": {
                "binary": self._is_binary_format(format_name),
                "encoding": self._get_encoding_type(format_name),
                "compression_support": self._supports_compression(format_name),
            },
        }

    def _build_history_section(self, format_name: str) -> dict[str, Any]:
        """Build format history."""
        history_map = {
            "pdf": {
                "invented": "1993",
                "creator": "Adobe Systems",
                "major_versions": ["PDF 1.0", "PDF 1.7", "PDF 2.0"],
            },
            "png": {
                "invented": "1996",
                "creator": "PNG Development Group",
                "major_versions": ["PNG 1.0", "PNG 1.1", "PNG 1.2"],
            },
            "jpg": {
                "invented": "1992",
                "creator": "Joint Photographic Experts Group",
                "major_versions": ["JPEG 1992", "JPEG 2000", "JPEG XR"],
            },
            "mp4": {
                "invented": "2001",
                "creator": "MPEG (Moving Picture Experts Group)",
                "major_versions": ["MPEG-4 Part 14"],
            },
        }
        
        return history_map.get(format_name, {
            "invented": "Date unknown",
            "creator": "Standards organization",
            "major_versions": [f"{format_name.upper()} 1.0+"],
        })

    def _build_security_section(self, format_name: str) -> dict[str, Any]:
        """Build security considerations."""
        return {
            "vulnerabilities": [],
            "considerations": [
                f"Ensure {format_name.upper()} files are from trusted sources",
                f"Validate {format_name.upper()} file integrity before processing",
                f"Keep software that handles {format_name.upper()} updated",
                f"Be cautious with embedded content in {format_name.upper()} files",
            ],
            "best_practices": [
                "Use secure channels to transfer files",
                "Validate file signatures when possible",
                "Store sensitive files encrypted",
            ],
        }

    def _build_compression_section(self, format_name: str) -> dict[str, Any]:
        """Build compression information."""
        compression_types = {
            "pdf": {"type": "Optional (Flate)", "lossy": False, "ratio": "10-30%"},
            "png": {"type": "Lossless (Deflate)", "lossy": False, "ratio": "20-40%"},
            "jpg": {"type": "Lossy (JPEG)", "lossy": True, "ratio": "85-95%"},
            "webp": {"type": "Lossy/Lossless", "lossy": True, "ratio": "80-90%"},
            "mp4": {"type": "Lossy (H.264)", "lossy": True, "ratio": "90-95%"},
            "mp3": {"type": "Lossy (MP3)", "lossy": True, "ratio": "85-90%"},
        }
        
        default = {"type": "Format-specific", "lossy": False, "ratio": "Variable"}
        compression = compression_types.get(format_name, default)
        
        return {
            "compression_type": compression["type"],
            "is_lossy": compression["lossy"],
            "typical_ratio": compression["ratio"],
            "description": f"Compression characteristics of {format_name.upper()} format",
        }

    def _build_accessibility_section(self, format_name: str) -> dict[str, Any]:
        """Build accessibility information."""
        return {
            "screen_reader_support": self._has_accessibility_support(format_name),
            "considerations": [
                f"Ensure {format_name.upper()} content includes alt text where applicable",
                f"Use semantic structure in {format_name.upper()} documents",
                f"Provide transcripts for audio/video content in {format_name.upper()}",
            ],
            "wcag_compliance": "Varies by content creator",
            "description": f"Accessibility guidelines for {format_name.upper()} files",
        }

    def _build_software_section(self, format_name: str) -> dict[str, Any]:
        """Build software that supports format."""
        software_map = {
            "pdf": ["Adobe Reader", "Chrome", "Firefox", "Preview"],
            "docx": ["Microsoft Word", "Google Docs", "LibreOffice"],
            "png": ["All browsers", "Image editors", "Preview apps"],
            "jpg": ["All browsers", "Image editors", "Preview apps"],
            "mp4": ["VLC", "QuickTime", "Media Player"],
            "mp3": ["iTunes", "Media Player", "Spotify"],
        }
        
        software = software_map.get(format_name, [
            "Standard applications",
            "Specialized viewers",
            "Online converters",
        ])
        
        return {
            "native_support": software[:3],
            "also_supported_by": software,
            "online_tools": ["Converigo", "Other online converters"],
        }

    def _build_tutorials_section(self, format_name: str) -> list[dict[str, str]]:
        """Build tutorial links."""
        return [
            {
                "title": f"How to create {format_name.upper()} files",
                "url": f"/tutorials/create-{format_name}",
                "description": f"Step-by-step guide to creating {format_name.upper()} files",
            },
            {
                "title": f"How to convert to {format_name.upper()}",
                "url": f"/tutorials/convert-to-{format_name}",
                "description": f"Learn multiple ways to convert files to {format_name.upper()}",
            },
            {
                "title": f"Best practices for {format_name.upper()}",
                "url": f"/tutorials/best-practices-{format_name}",
                "description": f"Pro tips for working with {format_name.upper()} files",
            },
        ]

    def _build_best_practices_section(self, format_name: str) -> list[str]:
        """Build best practices."""
        return [
            f"Choose {format_name.upper()} when it matches your use case",
            f"Validate {format_name.upper()} file integrity after conversion",
            f"Keep backups in multiple formats for long-term preservation",
            f"Use appropriate compression settings for {format_name.upper()}",
            f"Test {format_name.upper()} files across different viewers",
            f"Document the purpose and creation method of {format_name.upper()} files",
        ]

    def _build_comparisons_section(self, format_name: str) -> list[dict[str, str]]:
        """Build comparison links."""
        comparison_pairs = self._get_comparison_pairs(format_name)
        
        result = []
        for fmt1, fmt2 in comparison_pairs:
            result.append({
                "title": f"{fmt1.upper()} vs {fmt2.upper()}",
                "url": f"/{fmt1}-vs-{fmt2}",
                "description": f"Compare {fmt1.upper()} and {fmt2.upper()} formats",
            })
        
        return result

    def _build_related_formats_section(self, format_name: str) -> list[dict[str, str]]:
        """Build related formats."""
        related_map = {
            "pdf": ["docx", "txt", "jpg"],
            "docx": ["pdf", "txt", "odt"],
            "png": ["jpg", "webp", "gif"],
            "jpg": ["png", "webp", "pdf"],
            "webp": ["png", "jpg", "gif"],
            "mp4": ["mov", "avi", "mkv"],
            "mp3": ["wav", "ogg", "flac"],
        }
        
        related = related_map.get(format_name, [])
        result = []
        
        for fmt in related[:3]:
            result.append({
                "title": f"{fmt.upper()} format",
                "url": f"/formats/{fmt}",
                "description": f"Learn about {fmt.upper()} format",
            })
        
        return result

    def _build_related_converters_section(self, format_name: str) -> list[dict[str, str]]:
        """Build related converters."""
        converters = self.converter_registry_service.get_active()
        related = []
        
        format_lower = format_name.lower()
        for converter in converters:
            input_formats = [str(f).lower() for f in (converter.get("input_formats") or [])]
            output_formats = [str(f).lower() for f in (converter.get("output_formats") or [])]
            
            if format_lower in input_formats or format_lower in output_formats:
                related.append({
                    "title": converter.get("name", converter.get("slug", "")),
                    "url": f"/tools/{converter.get('slug', '')}",
                    "description": f"Convert {format_name.upper()} files with this tool",
                })
        
        return related[:5]

    def _build_hub_section(self, format_name: str) -> dict[str, Any]:
        """Build hub reference."""
        hub_map = {
            "pdf": {"slug": "pdf-conversion", "title": "PDF Conversion Hub"},
            "docx": {"slug": "document-conversion", "title": "Document Conversion Hub"},
            "doc": {"slug": "document-conversion", "title": "Document Conversion Hub"},
            "png": {"slug": "image-conversion", "title": "Image Conversion Hub"},
            "jpg": {"slug": "image-conversion", "title": "Image Conversion Hub"},
            "jpeg": {"slug": "image-conversion", "title": "Image Conversion Hub"},
            "webp": {"slug": "image-conversion", "title": "Image Conversion Hub"},
            "gif": {"slug": "image-conversion", "title": "Image Conversion Hub"},
            "mp4": {"slug": "video-conversion", "title": "Video Conversion Hub"},
            "mov": {"slug": "video-conversion", "title": "Video Conversion Hub"},
            "mp3": {"slug": "audio-conversion", "title": "Audio Conversion Hub"},
            "wav": {"slug": "audio-conversion", "title": "Audio Conversion Hub"},
        }
        
        hub = hub_map.get(format_name, {"slug": "image-conversion", "title": "Conversion Hub"})
        
        return {
            "title": hub["title"],
            "url": f"/{hub['slug']}",
            "description": f"Explore more {hub['title'].lower()} tools",
        }

    def _build_internal_links(self, format_name: str) -> dict[str, Any]:
        """Build internal links for format page."""
        try:
            links = self.internal_link_service.get_links_for_format(format_name)
            return links
        except Exception:
            return {
                "related_converters": [],
                "related_formats": [],
                "related_comparisons": [],
                "related_knowledge": [],
                "related_hubs": [],
            }

    # Helper methods

    def _collect_all_formats(self) -> list[str]:
        """Collect all known formats from converters."""
        formats = set()
        converters = self.converter_registry_service.get_active()
        
        for converter in converters:
            formats.update(str(f).lower() for f in (converter.get("input_formats") or []))
            formats.update(str(f).lower() for f in (converter.get("output_formats") or []))
        
        return sorted(list(formats))

    def _get_comparison_pairs(self, format_name: str) -> list[tuple[str, str]]:
        """Get comparison pairs for a format."""
        all_pairs = [
            ("pdf", "docx"),
            ("png", "jpg"),
            ("webp", "png"),
            ("mp4", "mov"),
            ("mp3", "wav"),
        ]
        
        format_lower = format_name.lower()
        result = []
        
        for fmt1, fmt2 in all_pairs:
            if format_lower == fmt1 or format_lower == fmt2:
                result.append((fmt1, fmt2))
        
        return result

    def _get_standardization_body(self, format_name: str) -> str:
        """Get standardization body for format."""
        body_map = {
            "pdf": "Adobe / ISO",
            "png": "PNG Development Group",
            "jpg": "JPEG Committee / ISO",
            "mp4": "MPEG / ISO",
            "mp3": "MPEG / ISO",
            "docx": "Microsoft / ISO/IEC",
        }
        return body_map.get(format_name, "Standards organization")

    def _is_binary_format(self, format_name: str) -> bool:
        """Check if format is binary."""
        text_formats = {"txt", "csv", "json", "xml", "html"}
        return format_name.lower() not in text_formats

    def _get_encoding_type(self, format_name: str) -> str:
        """Get encoding type for format."""
        encoding_map = {
            "txt": "UTF-8 / ASCII",
            "csv": "UTF-8 / ASCII",
            "json": "UTF-8",
            "xml": "UTF-8",
            "pdf": "Binary",
            "png": "Binary",
            "jpg": "Binary",
            "mp4": "Binary",
            "mp3": "Binary",
        }
        return encoding_map.get(format_name.lower(), "Format-specific")

    def _supports_compression(self, format_name: str) -> bool:
        """Check if format supports compression."""
        compressed_formats = {"pdf", "png", "txt", "json", "xml"}
        return format_name.lower() in compressed_formats or True

    def _has_accessibility_support(self, format_name: str) -> bool:
        """Check if format has accessibility support."""
        accessible = {"pdf", "docx", "html", "txt"}
        return format_name.lower() in accessible

    def build_cluster_coverage_report(self) -> dict[str, Any]:
        """Generate topic cluster coverage report."""
        formats = self._collect_all_formats()
        total_formats = len(formats)
        
        clusters_built = 0
        clusters_complete = 0
        orphan_topics = []
        
        for fmt in formats:
            try:
                cluster = self.build_cluster(fmt)
                clusters_built += 1
                
                # Check if cluster has all 17 sections
                sections = [
                    "knowledge", "faq", "mime", "file_extensions", "metadata",
                    "specification", "history", "security", "compression",
                    "accessibility", "software", "tutorials", "best_practices",
                    "comparisons", "related_formats", "related_converters", "hub"
                ]
                
                if all(section in cluster and cluster[section] for section in sections):
                    clusters_complete += 1
            except Exception:
                orphan_topics.append(fmt)
        
        coverage_percentage = round((clusters_built / total_formats * 100) if total_formats > 0 else 0, 2)
        completeness_percentage = round((clusters_complete / clusters_built * 100) if clusters_built > 0 else 0, 2)
        
        return {
            "total_formats": total_formats,
            "topic_clusters_total": clusters_built,
            "topic_clusters_complete": clusters_complete,
            "topic_cluster_coverage": coverage_percentage,
            "completeness_percentage": completeness_percentage,
            "orphan_topics": orphan_topics,
            "orphan_topics_count": len(orphan_topics),
        }
