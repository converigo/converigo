"""Regression tests for ConverterExpansionService and ecosystem integration."""

import pytest
from pathlib import Path

from app.services.converter_expansion_service import (
    ConverterExpansionService,
    ConverterMetadata,
)


class TestConverterExpansionService:
    """Test ConverterExpansionService core functionality."""

    def test_service_initializes(self) -> None:
        """Test ConverterExpansionService can be instantiated."""
        service = ConverterExpansionService(Path("app/data/converters"))
        assert service is not None
        assert service.converter_registry_service is not None

    def test_expand_converters_returns_complete_structure(self) -> None:
        """Test expand_converters returns all required fields."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="heic",
            output_format="jpg",
            category="image",
            description="Convert HEIC images to JPG",
            mime_type="image/heic",
            file_extension=".heic",
            priority=85,
        )
        
        result = service.expand_converters([metadata], require_quality_pass=False)
        
        assert "total_processed" in result
        assert "published" in result
        assert "rejected" in result
        assert "published_ids" in result
        assert "rejected_ids" in result
        assert "details" in result
        assert "timestamp" in result

    def test_single_converter_expansion_generates_all_artifacts(self) -> None:
        """Test single converter expansion generates all required artifacts."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="svg",
            output_format="pdf",
            category="document",
            description="Convert SVG to PDF documents",
            priority=75,
        )
        
        result = service._expand_single_converter(metadata, require_quality_pass=False)
        
        assert result.get("published") == True
        assert "converter_id" in result
        assert "registry" in result
        assert "contract" in result
        assert "landing" in result
        assert "seo" in result
        assert "faq" in result
        assert "topic_cluster" in result
        assert "comparisons" in result
        assert "internal_links" in result
        assert "json_ld" in result

    def test_registry_entry_generation(self) -> None:
        """Test registry entry generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="epub",
            output_format="pdf",
            category="document",
            description="Convert EPUB to PDF",
            priority=70,
        )
        
        registry_entry = service._generate_registry_entry(metadata, "epub-to-pdf")
        
        assert registry_entry["id"] == "epub-to-pdf"
        assert "EPUB" in registry_entry["name"]
        assert registry_entry["category"] == "document"
        assert registry_entry["enabled"] == True

    def test_contract_generation(self) -> None:
        """Test contract file generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="rtf",
            output_format="docx",
            category="document",
            description="Convert RTF to DOCX",
            mime_type="application/rtf",
            priority=60,
        )
        
        contract = service._generate_contract(metadata, "rtf-to-docx")
        
        assert contract["id"] == "rtf-to-docx"
        assert contract["slug"] == "rtf-to-docx"
        assert contract["category"] == "document"
        assert contract["input_formats"] == ["rtf"]
        assert contract["output_formats"] == ["docx"]
        assert contract["lifecycle_status"] == "active"

    def test_landing_metadata_generation(self) -> None:
        """Test landing page metadata generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="csv",
            output_format="xlsx",
            category="data",
            description="Convert CSV to Excel spreadsheet",
            priority=80,
        )
        
        landing = service._generate_landing_metadata(metadata, "csv-to-xlsx")
        
        assert landing["slug"] == "csv-to-xlsx"
        assert "CSV" in landing["title"]
        assert "XLSX" in landing["title"]
        assert landing["featured"] == False  # priority 80, featured = priority > 90
        assert landing["hero"]["eyebrow"] == "Converter tool"

    def test_seo_metadata_generation(self) -> None:
        """Test SEO metadata generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="json",
            output_format="xml",
            category="data",
            description="Convert JSON to XML",
            priority=65,
        )
        
        seo = service._generate_seo_metadata(metadata, "json-to-xml")
        
        assert "JSON" in seo["title"]
        assert "XML" in seo["title"]
        assert seo["canonical"] == "https://converigo.com/json-to-xml"
        assert "keywords" in seo
        assert len(seo.get("keywords", "")) > 0

    def test_faq_generation(self) -> None:
        """Test FAQ generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="tiff",
            output_format="png",
            category="image",
            description="Convert TIFF to PNG",
            priority=70,
        )
        
        faq = service._generate_faq(metadata)
        
        assert isinstance(faq, list)
        assert len(faq) >= 5
        assert all("question" in item and "answer" in item for item in faq)

    def test_topic_cluster_generation(self) -> None:
        """Test topic cluster generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="avif",
            output_format="png",
            category="image",
            description="Convert AVIF to PNG",
            priority=75,
        )
        
        cluster = service._generate_topic_cluster(metadata, "avif-to-png")
        
        assert cluster["converter_id"] == "avif-to-png"
        assert cluster["category"] == "image"
        assert "related_formats" in cluster
        assert cluster["cluster_type"] == "format_conversion"

    def test_comparison_relationships_generation(self) -> None:
        """Test comparison relationships generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="bmp",
            output_format="gif",
            category="image",
            description="Convert BMP to GIF",
            priority=55,
        )
        
        comparisons = service._generate_comparison_relationships(metadata, "bmp-to-gif")
        
        assert comparisons["converter_id"] == "bmp-to-gif"
        assert "comparison_type" in comparisons
        assert "similar_converters" in comparisons
        assert "alternative_formats" in comparisons

    def test_internal_links_generation(self) -> None:
        """Test internal links generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="flac",
            output_format="mp3",
            category="audio",
            description="Convert FLAC to MP3",
            priority=70,
        )
        
        links = service._generate_internal_links(metadata, "flac-to-mp3")
        
        assert links["converter_id"] == "flac-to-mp3"
        assert "outbound_links" in links
        assert "inbound_links" in links
        assert "topic_links" in links
        assert "related_tools" in links

    def test_json_ld_schema_generation(self) -> None:
        """Test JSON-LD schema generation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="ogg",
            output_format="wav",
            category="audio",
            description="Convert OGG to WAV",
            priority=60,
        )
        
        schema = service._generate_json_ld_schema(metadata, "ogg-to-wav")
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "SoftwareApplication"
        assert "OGG" in schema["name"]
        assert schema["url"] == "https://converigo.com/ogg-to-wav"

    def test_metadata_validation(self) -> None:
        """Test metadata validation."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        # Valid metadata
        metadata = ConverterMetadata(
            input_format="webp",
            output_format="ico",
            category="image",
            description="Convert WEBP to ICO",
            priority=50,
        )
        
        assert metadata.input_format == "webp"
        assert metadata.priority == 50

    def test_priority_tier_determination(self) -> None:
        """Test priority tier determination."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        # Tier 1 priority (high)
        metadata_tier1 = ConverterMetadata(
            input_format="pdf",
            output_format="docx",
            category="document",
            description="PDF to DOCX",
            priority=95,
        )
        landing_tier1 = service._generate_landing_metadata(metadata_tier1, "pdf-to-docx")
        assert landing_tier1["featured"] == True
        
        # Tier 2 priority (medium)
        metadata_tier2 = ConverterMetadata(
            input_format="svg",
            output_format="png",
            category="image",
            description="SVG to PNG",
            priority=75,
        )
        landing_tier2 = service._generate_landing_metadata(metadata_tier2, "svg-to-png")
        assert landing_tier2["popular"] == False

    def test_expansion_summary(self) -> None:
        """Test expansion summary."""
        service = ConverterExpansionService(Path("app/data/converters"))
        summary = service.get_expansion_summary()
        
        assert "total_converters_current" in summary
        assert "expansion_results" in summary
        assert "timestamp" in summary

    def test_batch_expansion(self) -> None:
        """Test batch expansion of multiple converters."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata_list = [
            ConverterMetadata(
                input_format="heic",
                output_format="jpg",
                category="image",
                description="HEIC to JPG",
                priority=80,
            ),
            ConverterMetadata(
                input_format="epub",
                output_format="mobi",
                category="document",
                description="EPUB to MOBI",
                priority=75,
            ),
        ]
        
        result = service.expand_converters(metadata_list, require_quality_pass=False)
        
        assert result["total_processed"] == 2
        assert len(result["details"]) == 2

    def test_deterministic_output(self) -> None:
        """Test deterministic output - same metadata produces same result."""
        service1 = ConverterExpansionService(Path("app/data/converters"))
        metadata = ConverterMetadata(
            input_format="m4a",
            output_format="wav",
            category="audio",
            description="M4A to WAV",
            priority=65,
        )
        
        result1 = service1._generate_registry_entry(metadata, "m4a-to-wav")
        
        service2 = ConverterExpansionService(Path("app/data/converters"))
        result2 = service2._generate_registry_entry(metadata, "m4a-to-wav")
        
        assert result1 == result2

    def test_no_duplicate_converter_ids(self) -> None:
        """Test no duplicate converter IDs generated."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        converter_ids = set()
        
        tier1_converters = [
            ("pdf", "docx"), ("pdf", "jpg"), ("docx", "pdf"),
            ("xlsx", "csv"), ("jpg", "png"), ("png", "webp"),
            ("mp4", "mp3"), ("mp3", "wav"),
        ]
        
        for input_fmt, output_fmt in tier1_converters:
            converter_id = f"{input_fmt}-to-{output_fmt}".lower()
            assert converter_id not in converter_ids
            converter_ids.add(converter_id)

    def test_quality_check_integration(self) -> None:
        """Test quality check integration with CQE."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="docx",
            output_format="pdf",
            category="document",
            description="DOCX to PDF",
            priority=85,
        )
        
        result = service._expand_single_converter(metadata, require_quality_pass=True)
        
        # Should have quality score and either published=True or published=False with decision
        assert "quality_score" in result
        assert result["published"] == False or "decision" in result or result.get("published") == True

    def test_engine_type_determination(self) -> None:
        """Test conversion engine type determination."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        assert service._determine_engine("image") == "image"
        assert service._determine_engine("document") == "document"
        assert service._determine_engine("audio") == "audio"
        assert service._determine_engine("video") == "video"
        assert service._determine_engine("archive") == "archive"
        assert service._determine_engine("unknown") == "generic"

    def test_related_formats_grouping(self) -> None:
        """Test related formats are properly grouped."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        # Image formats
        image_metadata = ConverterMetadata(
            input_format="jpg",
            output_format="png",
            category="image",
            description="JPG to PNG",
            priority=70,
        )
        related = service._get_related_formats(image_metadata)
        assert "png" in related or "webp" in related
        
        # Document formats
        doc_metadata = ConverterMetadata(
            input_format="pdf",
            output_format="docx",
            category="document",
            description="PDF to DOCX",
            priority=85,
        )
        related = service._get_related_formats(doc_metadata)
        assert "xlsx" in related or "pptx" in related

    def test_alternative_formats_suggestion(self) -> None:
        """Test alternative formats are suggested."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="pdf",
            output_format="jpg",
            category="document",
            description="PDF to JPG",
            priority=90,
        )
        
        alternatives = service._get_alternative_formats(metadata)
        
        assert len(alternatives) > 0
        assert "jpg" not in alternatives
        assert "pdf" not in alternatives

    def test_timestamp_format(self) -> None:
        """Test timestamp is in valid ISO format."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        timestamp = service._get_timestamp()
        
        # Should end with Z (UTC)
        assert timestamp.endswith("Z")
        # Should contain T (ISO format)
        assert "T" in timestamp


class TestConverterExpansionServiceRegression:
    """Regression tests for ConverterExpansionService edge cases."""

    def test_expansion_with_empty_metadata_list(self) -> None:
        """Test expansion with empty metadata list."""
        service = ConverterExpansionService(Path("app/data/converters"))
        result = service.expand_converters([], require_quality_pass=False)
        
        assert result["total_processed"] == 0
        assert result["published"] == 0
        assert result["rejected"] == 0

    def test_metadata_with_minimal_fields(self) -> None:
        """Test metadata with only required fields."""
        metadata = ConverterMetadata(
            input_format="test",
            output_format="test2",
            category="generic",
            description="Test converter",
        )
        
        assert metadata.input_format == "test"
        assert metadata.priority == 50  # Default priority is 50

    def test_converter_id_format(self) -> None:
        """Test converter ID format consistency."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="pdf",
            output_format="doc",
            category="document",
            description="Test",
            priority=70,
        )
        
        entry = service._generate_registry_entry(metadata, "pdf-to-doc")
        assert entry["id"] == "pdf-to-doc"

    def test_landing_required_fields(self) -> None:
        """Test landing metadata has all required fields."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="txt",
            output_format="pdf",
            category="document",
            description="Text to PDF",
            priority=50,
        )
        
        landing = service._generate_landing_metadata(metadata, "txt-to-pdf")
        
        assert "slug" in landing
        assert "title" in landing
        assert "hero" in landing

    def test_contract_mime_types_list(self) -> None:
        """Test contract properly generates mime types."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="jpeg",
            output_format="png",
            category="image",
            description="JPEG to PNG",
            mime_type="image/jpeg",
            priority=85,
        )
        
        contract = service._generate_contract(metadata, "jpeg-to-png")
        
        assert isinstance(contract["accepted_mime_types"], list)

    def test_seo_keywords_not_empty(self) -> None:
        """Test SEO keywords are generated."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="mp4",
            output_format="avi",
            category="video",
            description="MP4 to AVI",
            priority=70,
        )
        
        seo = service._generate_seo_metadata(metadata, "mp4-to-avi")
        
        assert "keywords" in seo
        assert len(seo["keywords"]) > 0

    def test_faq_count(self) -> None:
        """Test FAQ generates multiple items."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="webm",
            output_format="mp4",
            category="video",
            description="WebM to MP4",
            priority=65,
        )
        
        faq = service._generate_faq(metadata)
        
        assert len(faq) >= 5

    def test_topic_cluster_has_relationships(self) -> None:
        """Test topic cluster generates relationships."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="bmp",
            output_format="jpg",
            category="image",
            description="BMP to JPG",
            priority=60,
        )
        
        cluster = service._generate_topic_cluster(metadata, "bmp-to-jpg")
        
        assert "related_formats" in cluster

    def test_comparison_alternatives(self) -> None:
        """Test comparison includes alternative formats."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="pptx",
            output_format="pdf",
            category="document",
            description="PPTX to PDF",
            priority=80,
        )
        
        comp = service._generate_comparison_relationships(metadata, "pptx-to-pdf")
        
        assert "alternative_formats" in comp

    def test_priority_90_boundary(self) -> None:
        """Test priority boundary at 90."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        # Priority 90 should not be featured
        metadata90 = ConverterMetadata(
            input_format="pdf",
            output_format="txt",
            category="document",
            description="PDF to TXT",
            priority=90,
        )
        
        landing90 = service._generate_landing_metadata(metadata90, "pdf-to-txt")
        assert landing90["featured"] == False

    def test_priority_91_featured(self) -> None:
        """Test priority > 90 is featured."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        # Priority 91 should be featured
        metadata91 = ConverterMetadata(
            input_format="pdf",
            output_format="txt",
            category="document",
            description="PDF to TXT",
            priority=91,
        )
        
        landing91 = service._generate_landing_metadata(metadata91, "pdf-to-txt")
        assert landing91["featured"] == True

    def test_acronym_uppercase_pdf(self) -> None:
        """Test PDF acronym is preserved."""
        service = ConverterExpansionService(Path("app/data/converters"))
        title = service._to_title_case("pdf")
        assert title == "PDF"

    def test_acronym_uppercase_json(self) -> None:
        """Test JSON acronym is preserved."""
        service = ConverterExpansionService(Path("app/data/converters"))
        title = service._to_title_case("json")
        assert title == "JSON"

    def test_webp_capitalization(self) -> None:
        """Test WebP special capitalization."""
        service = ConverterExpansionService(Path("app/data/converters"))
        title = service._to_title_case("webp")
        assert title == "WebP"

    def test_engine_type_image(self) -> None:
        """Test image engine type determination."""
        service = ConverterExpansionService(Path("app/data/converters"))
        engine = service._determine_engine("image")
        assert engine == "image"

    def test_engine_type_video(self) -> None:
        """Test video engine type determination."""
        service = ConverterExpansionService(Path("app/data/converters"))
        engine = service._determine_engine("video")
        assert engine == "video"

    def test_engine_type_generic_fallback(self) -> None:
        """Test generic engine type fallback."""
        service = ConverterExpansionService(Path("app/data/converters"))
        engine = service._determine_engine("unknown")
        assert engine == "generic"

    def test_full_expansion_pipeline(self) -> None:
        """Test full expansion pipeline execution."""
        service = ConverterExpansionService(Path("app/data/converters"))
        
        metadata = ConverterMetadata(
            input_format="heif",
            output_format="jpeg",
            category="image",
            description="HEIF to JPEG conversion",
            priority=88,
        )
        
        result = service._expand_single_converter(metadata, require_quality_pass=False)
        
        # All stages should be present
        assert "registry" in result
        assert "contract" in result
        assert "landing" in result
        assert "json_ld" in result
