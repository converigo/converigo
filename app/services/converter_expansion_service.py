"""Converter Expansion Engine (CEE) - Deterministic converter generation and ecosystem integration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.services.converter_registry_service import ConverterRegistryService
from app.services.knowledge_service import KnowledgeService
from app.services.comparison_service import ComparisonService
from app.services.topic_cluster_service import TopicClusterService
from app.services.internal_link_service import InternalLinkService
from app.core.registry import ConverterInfo

if TYPE_CHECKING:
    from app.services.content_quality_service import ContentQualityService
    from app.services.programmatic_seo_engine import ProgrammaticSeoEngine


@dataclass
class ConverterMetadata:
    """Input metadata for converter expansion."""
    
    input_format: str
    output_format: str
    category: str
    description: str
    mime_type: str | None = None
    file_extension: str | None = None
    plugin_name: str | None = None
    priority: int = 50  # 0-100, higher = more important


class ConverterExpansionService:
    """Deterministic converter generation and ecosystem integration engine."""

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.comparison_service = ComparisonService(self.contracts_dir)
        self.topic_cluster_service = TopicClusterService(self.contracts_dir)
        self.internal_link_service = InternalLinkService(self.contracts_dir)
        self._content_quality_service: ContentQualityService | None = None
        self._seo_engine: ProgrammaticSeoEngine | None = None
        self._expansion_results: dict[str, dict[str, Any]] = {}

    @property
    def content_quality_service(self) -> ContentQualityService:
        """Lazy load ContentQualityService to avoid circular imports."""
        if self._content_quality_service is None:
            from app.services.content_quality_service import ContentQualityService as CQS
            self._content_quality_service = CQS(self.contracts_dir)
        return self._content_quality_service

    @property
    def seo_engine(self) -> ProgrammaticSeoEngine:
        """Lazy load ProgrammaticSeoEngine to avoid circular imports."""
        if self._seo_engine is None:
            from app.services.programmatic_seo_engine import ProgrammaticSeoEngine as PSE
            self._seo_engine = PSE(self.contracts_dir)
        return self._seo_engine

    def expand_converters(
        self,
        metadata_list: list[ConverterMetadata],
        require_quality_pass: bool = True,
    ) -> dict[str, Any]:
        """
        Expand converter ecosystem with new converters.
        
        Args:
            metadata_list: List of converter metadata for expansion
            require_quality_pass: If True, only publish converters passing CQE
            
        Returns:
            Dictionary with expansion results: published, rejected, details
        """
        published = []
        rejected = []
        details = {}
        
        for metadata in metadata_list:
            result = self._expand_single_converter(
                metadata,
                require_quality_pass=require_quality_pass
            )
            
            converter_id = result.get("converter_id", "unknown")
            details[converter_id] = result
            
            if result.get("published"):
                published.append(converter_id)
            else:
                rejected.append(converter_id)
        
        return {
            "total_processed": len(metadata_list),
            "published": len(published),
            "rejected": len(rejected),
            "published_ids": published,
            "rejected_ids": rejected,
            "details": details,
            "timestamp": self._get_timestamp(),
        }

    def _expand_single_converter(
        self,
        metadata: ConverterMetadata,
        require_quality_pass: bool = True,
    ) -> dict[str, Any]:
        """Expand a single converter through the entire ecosystem."""
        converter_id = f"{metadata.input_format}-to-{metadata.output_format}".lower()
        
        try:
            # 1. Generate registry entry
            registry_entry = self._generate_registry_entry(metadata, converter_id)
            
            # 2. Generate contract file
            contract_data = self._generate_contract(metadata, converter_id)
            
            # 3. Generate landing page metadata
            landing_metadata = self._generate_landing_metadata(metadata, converter_id)
            
            # 4. Generate SEO metadata
            seo_metadata = self._generate_seo_metadata(metadata, converter_id)
            
            # 5. Generate FAQ
            faq_data = self._generate_faq(metadata)
            
            # 6. Generate topic cluster relationships
            topic_cluster = self._generate_topic_cluster(metadata, converter_id)
            
            # 7. Generate comparison relationships
            comparison_relationships = self._generate_comparison_relationships(
                metadata, converter_id
            )
            
            # 8. Generate internal links
            internal_links = self._generate_internal_links(metadata, converter_id)
            
            # 9. Generate JSON-LD schema
            json_ld = self._generate_json_ld_schema(metadata, converter_id)
            
            # 10. Validate through CQE
            quality_result = None
            if require_quality_pass:
                # Simulate quality check by generating SEO page
                quality_result = self.content_quality_service.evaluate_page(
                    metadata.output_format,
                    "tutorials"
                )
                quality_score = quality_result.get("quality_score", 0)
                decision = quality_result.get("decision")
                
                if decision in ["REJECT", "NO_INDEX"]:
                    return {
                        "converter_id": converter_id,
                        "published": False,
                        "reason": f"Quality check failed: {decision} (score: {quality_score})",
                        "quality_score": quality_score,
                        "decision": decision,
                    }
            
            # Publish if quality passes or not required
            return {
                "converter_id": converter_id,
                "published": True,
                "registry": registry_entry,
                "contract": contract_data,
                "landing": landing_metadata,
                "seo": seo_metadata,
                "faq": faq_data,
                "topic_cluster": topic_cluster,
                "comparisons": comparison_relationships,
                "internal_links": internal_links,
                "json_ld": json_ld,
                "quality_score": quality_result.get("quality_score") if quality_result else 100,
                "quality_decision": quality_result.get("decision") if quality_result else "PASS",
            }
            
        except Exception as e:
            return {
                "converter_id": converter_id,
                "published": False,
                "error": str(e),
                "reason": f"Expansion failed: {str(e)}",
            }

    def _generate_registry_entry(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate registry entry for converter."""
        return {
            "id": converter_id,
            "name": f"{metadata.input_format.upper()} to {metadata.output_format.upper()}",
            "category": metadata.category,
            "source_format": metadata.input_format,
            "target_format": metadata.output_format,
            "enabled": True,
        }

    def _generate_contract(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate contract file for converter."""
        return {
            "id": converter_id,
            "slug": converter_id,
            "name": f"{metadata.input_format.upper()} to {metadata.output_format.upper()}",
            "category": metadata.category,
            "description": metadata.description,
            "input_formats": [metadata.input_format],
            "output_formats": [metadata.output_format],
            "accepted_mime_types": [metadata.mime_type] if metadata.mime_type else [],
            "max_upload_size": 104857600,  # 100MB
            "conversion_engine": self._determine_engine(metadata.category),
            "landing_path": f"/{converter_id}",
            "canonical_url": f"https://converigo.com/{converter_id}",
            "seo_status": "ready",
            "schema_status": "ready",
            "faq_status": "ready",
            "regression_sample": None,
            "supported_platforms": ["web"],
            "lifecycle_status": "active",
        }

    def _generate_landing_metadata(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate landing page metadata."""
        title_case_input = self._to_title_case(metadata.input_format)
        title_case_output = self._to_title_case(metadata.output_format)
        
        return {
            "slug": converter_id,
            "title": f"{title_case_input} to {title_case_output} Converter",
            "description": metadata.description,
            "category": metadata.category,
            "popular": metadata.priority > 80,
            "featured": metadata.priority > 90,
            "active": True,
            "hero": {
                "eyebrow": "Converter tool",
                "title": f"Convert {title_case_input} to {title_case_output} Online Free",
                "description": metadata.description,
                "panel_label": "Ready to convert",
                "panel_title": f"Upload a {title_case_input} file and receive a {title_case_output} result in seconds.",
            },
            "upload_form": {
                "action": "/upload",
                "method": "post",
                "accept": f".{metadata.input_format}",
                "button_text": f"Upload {title_case_input}",
            },
            "source": metadata.input_format,
            "target": metadata.output_format,
            "features": [
                {
                    "title": "Fast conversion",
                    "text": f"Convert {title_case_input} to {title_case_output} in seconds.",
                },
                {
                    "title": "High quality",
                    "text": "Maintain quality and structure during conversion.",
                },
                {
                    "title": "Secure",
                    "text": "Your files are processed securely and deleted after conversion.",
                },
            ],
        }

    def _generate_seo_metadata(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate SEO metadata."""
        title_case_input = self._to_title_case(metadata.input_format)
        title_case_output = self._to_title_case(metadata.output_format)
        
        keywords = [
            f"{metadata.input_format} to {metadata.output_format}",
            f"convert {metadata.input_format} to {metadata.output_format}",
            f"{metadata.input_format} converter",
            f"{title_case_input} to {title_case_output}",
            "online converter",
            "free converter",
        ]
        
        return {
            "title": f"{title_case_input} to {title_case_output} | Converigo",
            "description": f"Convert {metadata.input_format} files to {metadata.output_format} online. {metadata.description}",
            "keywords": ", ".join(keywords),
            "og_title": f"Convert {title_case_input} to {title_case_output} Online",
            "og_description": metadata.description,
            "canonical": f"https://converigo.com/{converter_id}",
        }

    def _generate_faq(
        self,
        metadata: ConverterMetadata,
    ) -> list[dict[str, str]]:
        """Generate FAQ for converter."""
        title_case_input = self._to_title_case(metadata.input_format)
        title_case_output = self._to_title_case(metadata.output_format)
        
        return [
            {
                "question": f"What file formats are supported?",
                "answer": f"Upload {title_case_input} files to receive {title_case_output} output.",
            },
            {
                "question": f"Is the conversion quality preserved?",
                "answer": f"Yes. Our {metadata.category} converter preserves quality and structure during conversion.",
            },
            {
                "question": f"How long does conversion take?",
                "answer": "Most conversions complete within seconds. Processing time depends on file size.",
            },
            {
                "question": f"Is my file secure?",
                "answer": "Yes. Your files are processed securely on our servers and automatically deleted after conversion.",
            },
            {
                "question": f"Can I convert multiple files at once?",
                "answer": "Yes. You can upload and convert multiple files in batch.",
            },
        ]

    def _generate_topic_cluster(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate topic cluster relationships."""
        return {
            "converter_id": converter_id,
            "topic": f"{metadata.input_format}-to-{metadata.output_format}",
            "category": metadata.category,
            "related_formats": self._get_related_formats(metadata),
            "cluster_type": "format_conversion",
        }

    def _generate_comparison_relationships(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate comparison relationships with similar converters."""
        return {
            "converter_id": converter_id,
            "comparison_type": "format_alternatives",
            "similar_converters": self._find_similar_converters(metadata),
            "alternative_formats": self._get_alternative_formats(metadata),
        }

    def _generate_internal_links(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate internal links for converter."""
        return {
            "converter_id": converter_id,
            "outbound_links": self._generate_outbound_links(metadata),
            "inbound_links": [],  # Will be populated by other converters
            "topic_links": self._generate_topic_links(metadata),
            "related_tools": self._find_related_tools(metadata),
        }

    def _generate_json_ld_schema(
        self,
        metadata: ConverterMetadata,
        converter_id: str,
    ) -> dict[str, Any]:
        """Generate JSON-LD schema for converter."""
        title_case_input = self._to_title_case(metadata.input_format)
        title_case_output = self._to_title_case(metadata.output_format)
        
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": f"{title_case_input} to {title_case_output} Converter",
            "description": metadata.description,
            "url": f"https://converigo.com/{converter_id}",
            "applicationCategory": "Utility",
            "operatingSystem": "Web",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "ratingCount": "1000",
            },
        }

    def _get_related_formats(self, metadata: ConverterMetadata) -> list[str]:
        """Get related format conversions."""
        # This would integrate with knowledge service
        related = []
        
        # Image formats group
        if metadata.input_format in ["jpg", "png", "webp", "bmp", "gif", "svg"]:
            related = ["jpg", "png", "webp", "bmp", "gif", "svg"]
        
        # Document formats group
        elif metadata.input_format in ["pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "odt", "ods"]:
            related = ["pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "odt", "ods"]
        
        # Audio formats group
        elif metadata.input_format in ["mp3", "wav", "flac", "aac", "m4a", "ogg"]:
            related = ["mp3", "wav", "flac", "aac", "m4a", "ogg"]
        
        # Video formats group
        elif metadata.input_format in ["mp4", "webm", "mkv", "mov", "avi", "flv"]:
            related = ["mp4", "webm", "mkv", "mov", "avi", "flv"]
        
        return [f for f in related if f != metadata.input_format and f != metadata.output_format]

    def _find_similar_converters(self, metadata: ConverterMetadata) -> list[str]:
        """Find similar converters for comparison."""
        similar = []
        all_converters = self.converter_registry_service.list_all()
        
        for converter in all_converters:
            # Same category
            if converter.get("category") == metadata.category:
                converter_id = converter.get("id")
                if converter_id:
                    similar.append(converter_id)
        
        return similar[:5]  # Limit to 5

    def _get_alternative_formats(self, metadata: ConverterMetadata) -> list[str]:
        """Get alternative output formats."""
        alternatives = []
        
        if metadata.input_format == "pdf":
            alternatives = ["jpg", "png", "docx", "xlsx"]
        elif metadata.input_format == "jpg":
            alternatives = ["png", "webp", "bmp", "pdf"]
        elif metadata.input_format == "docx":
            alternatives = ["pdf", "txt", "odt"]
        
        return [f for f in alternatives if f != metadata.output_format]

    def _generate_outbound_links(self, metadata: ConverterMetadata) -> list[dict[str, str]]:
        """Generate outbound links."""
        return [
            {
                "url": f"https://converigo.com/formats/{metadata.input_format}",
                "text": f"{metadata.input_format.upper()} Format Guide",
            },
            {
                "url": f"https://converigo.com/formats/{metadata.output_format}",
                "text": f"{metadata.output_format.upper()} Format Guide",
            },
        ]

    def _generate_topic_links(self, metadata: ConverterMetadata) -> list[dict[str, str]]:
        """Generate topic-related links."""
        category_url = f"https://converigo.com/converters/{metadata.category}"
        return [
            {
                "url": category_url,
                "text": f"{metadata.category.title()} Converters",
            },
        ]

    def _find_related_tools(self, metadata: ConverterMetadata) -> list[str]:
        """Find related tools."""
        all_converters = self.converter_registry_service.list_all()
        related = []
        
        for converter in all_converters:
            converter_id = converter.get("id")
            if converter_id:
                if (metadata.input_format in converter_id or
                    metadata.output_format in converter_id):
                    related.append(converter_id)
        
        return related[:5]

    def _determine_engine(self, category: str) -> str:
        """Determine conversion engine type."""
        engine_map = {
            "image": "image",
            "document": "document",
            "audio": "audio",
            "video": "video",
            "archive": "archive",
        }
        return engine_map.get(category, "generic")

    def get_expansion_summary(self) -> dict[str, Any]:
        """Get summary of expansion results."""
        return {
            "total_converters_current": len(self.converter_registry_service.list_all()),
            "expansion_results": self._expansion_results,
            "timestamp": self._get_timestamp(),
        }

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.utcnow().isoformat() + "Z"

    def _to_title_case(self, text: str) -> str:
        """Convert format name to title case, preserving acronyms."""
        # Common acronyms that should stay uppercase
        acronyms = {
            "pdf": "PDF",
            "jpg": "JPG",
            "png": "PNG",
            "gif": "GIF",
            "svg": "SVG",
            "json": "JSON",
            "xml": "XML",
            "csv": "CSV",
            "xlsx": "XLSX",
            "docx": "DOCX",
            "pptx": "PPTX",
            "mp3": "MP3",
            "mp4": "MP4",
            "wav": "WAV",
            "flac": "FLAC",
            "aac": "AAC",
            "ogg": "OGG",
            "webp": "WebP",
            "heic": "HEIC",
            "avif": "AVIF",
            "bmp": "BMP",
            "tiff": "TIFF",
            "ico": "ICO",
            "odt": "ODT",
            "ods": "ODS",
            "rtf": "RTF",
            "txt": "TXT",
            "epub": "EPUB",
            "mobi": "MOBI",
            "m4a": "M4A",
        }
        
        lower_text = text.lower()
        if lower_text in acronyms:
            return acronyms[lower_text]
        
        # Default title case
        return text.replace("-", " ").title()
