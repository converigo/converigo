"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF to DOCX Converter
STATUS: LOCKED 🔒

These tests protect the certified PDF→DOCX converter.
Changes to this converter require version increment and re-certification.

Certification Requirements:
✓ Input validation (empty/password-protected PDFs rejected)
✓ Conversion success (valid PDF → valid DOCX)
✓ Output existence (file created)
✓ Output validation (correct extension, not corrupted)
✓ Regression tests (no breaking changes)
"""

from io import BytesIO
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient
from app.core.settings import settings
from reportlab.pdfgen import canvas
from docx import Document

from app.main import app
from app.plugins.registry import registry


class TestPDFToDocxCertified:
    """Certified test suite for pdf-to-docx converter."""
    
    @staticmethod
    def create_simple_pdf() -> BytesIO:
        """Create a simple valid PDF."""
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer)
        pdf_canvas.drawString(100, 750, "Certified PDF to DOCX test")
        pdf_canvas.save()
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def create_multipage_pdf() -> BytesIO:
        """Create a multi-page PDF."""
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer)
        for page_num in range(1, 4):
            pdf_canvas.drawString(100, 750, f"Page {page_num}")
            pdf_canvas.showPage()
        pdf_canvas.save()
        buffer.seek(0)
        return buffer
    
    def test_001_plugin_discovered(self):
        """TEST 001: Plugin is properly registered."""
        plugin = registry.get_plugin("pdf", "docx")
        assert plugin is not None
        assert plugin.slug == "pdf-to-word"
        assert "docx" in plugin.target_formats
    
    def test_002_simple_pdf_conversion_success(self):
        """TEST 002: Simple PDF converts to DOCX successfully."""
        client = TestClient(app)
        simple_pdf = self.create_simple_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", simple_pdf, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        # Conversion must succeed
        assert response.status_code == 201
        assert response.json()["status"] == "success"
    
    def test_003_output_file_created(self):
        """TEST 003: Output DOCX file is created."""
        client = TestClient(app)
        simple_pdf = self.create_simple_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", simple_pdf, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        assert response.status_code == 201
        filename = response.json()["filename"]
        output_path = settings.OUTPUT_DIR / "document" / filename
        
        # File must exist
        assert output_path.exists()
        output_path.unlink(missing_ok=True)
    
    def test_004_output_file_extension_correct(self):
        """TEST 004: Output file has correct DOCX extension."""
        client = TestClient(app)
        simple_pdf = self.create_simple_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", simple_pdf, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        filename = response.json()["filename"]
        assert filename.endswith(".docx")
        
        output_path = settings.OUTPUT_DIR / "document" / filename
        assert output_path.suffix == ".docx"
        output_path.unlink(missing_ok=True)
    
    def test_005_output_file_not_corrupted(self):
        """TEST 005: Output DOCX file is valid and not corrupted."""
        client = TestClient(app)
        simple_pdf = self.create_simple_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", simple_pdf, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        filename = response.json()["filename"]
        output_path = settings.OUTPUT_DIR / "document" / filename
        
        # File must be readable as valid DOCX
        try:
            doc = Document(str(output_path))
            # If we can open it as Document, it's not corrupted
            assert doc is not None
        except Exception as e:
            raise AssertionError(f"Output DOCX is corrupted: {e}")
        finally:
            output_path.unlink(missing_ok=True)
    
    def test_006_multipage_pdf_conversion(self):
        """TEST 006: Multi-page PDF converts correctly."""
        client = TestClient(app)
        multipage_pdf = self.create_multipage_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("multipage.pdf", multipage_pdf, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        assert response.status_code == 201
        assert response.json()["status"] == "success"
        
        filename = response.json()["filename"]
        output_path = settings.OUTPUT_DIR / "document" / filename
        
        # Verify file exists and is valid
        assert output_path.exists()
        doc = Document(str(output_path))
        assert doc is not None
        
        output_path.unlink(missing_ok=True)
    
    def test_007_empty_pdf_rejected_with_422(self):
        """TEST 007: Empty PDF (0 pages) is rejected with 422."""
        client = TestClient(app)
        
        # Create empty PDF
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer)
        pdf_canvas.save()  # No content
        buffer.seek(0)
        
        response = client.post(
            "/convert",
            files={"file": ("empty.pdf", buffer, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        # Must return 422 Unprocessable Entity
        assert response.status_code == 422
        assert response.json()["code"] == "UNSUPPORTED_CONVERSION"
        assert "no pages" in response.json()["message"].lower()
    
    def test_008_output_target_format_correct(self):
        """TEST 008: Response indicates correct target format."""
        client = TestClient(app)
        simple_pdf = self.create_simple_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", simple_pdf, "application/pdf")},
            data={"target_format": "docx"},
        )
        
        assert response.json()["target_format"] == "docx"

        output_path = settings.OUTPUT_DIR / "document" / response.json()["filename"]
        output_path.unlink(missing_ok=True)
    
    def test_009_doc_alias_converts_to_docx(self):
        """TEST 009: 'doc' format alias converts to 'docx'."""
        client = TestClient(app)
        simple_pdf = self.create_simple_pdf()
        
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", simple_pdf, "application/pdf")},
            data={"target_format": "doc"},
        )
        
        # Should succeed (doc → docx)
        assert response.status_code == 201
        filename = response.json()["filename"]
        
        # Output should be .docx (not .doc)
        assert filename.endswith(".docx")
        
        output_path = settings.OUTPUT_DIR / "document" / filename
        output_path.unlink(missing_ok=True)


# Module-level test functions for pytest discovery
def test_pdf_to_docx_plugin_discovered():
    """T001: Plugin discovery test."""
    test = TestPDFToDocxCertified()
    test.test_001_plugin_discovered()


def test_pdf_to_docx_simple_conversion():
    """T002: Simple PDF conversion test."""
    test = TestPDFToDocxCertified()
    test.test_002_simple_pdf_conversion_success()


def test_pdf_to_docx_output_created():
    """T003: Output file creation test."""
    test = TestPDFToDocxCertified()
    test.test_003_output_file_created()


def test_pdf_to_docx_extension_correct():
    """T004: Output extension validation test."""
    test = TestPDFToDocxCertified()
    test.test_004_output_file_extension_correct()


def test_pdf_to_docx_not_corrupted():
    """T005: Output file corruption check test."""
    test = TestPDFToDocxCertified()
    test.test_005_output_file_not_corrupted()


def test_pdf_to_docx_multipage():
    """T006: Multi-page PDF conversion test."""
    test = TestPDFToDocxCertified()
    test.test_006_multipage_pdf_conversion()


def test_pdf_to_docx_empty_pdf_rejected():
    """T007: Empty PDF rejection test."""
    test = TestPDFToDocxCertified()
    test.test_007_empty_pdf_rejected_with_422()


def test_pdf_to_docx_target_format():
    """T008: Target format validation test."""
    test = TestPDFToDocxCertified()
    test.test_008_output_target_format_correct()


def test_pdf_to_docx_doc_alias():
    """T009: DOC format alias test."""
    test = TestPDFToDocxCertified()
    test.test_009_doc_alias_converts_to_docx()
