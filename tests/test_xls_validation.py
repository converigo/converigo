"""XLS pair-scoped validation tests for Phase 6.3 boundary implementation."""

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

import app.utils.file_validator as file_validator_module
import app.services.upload_service as upload_service_module


@pytest.fixture
def reset_extension_validator(monkeypatch):
    """Reset file_validator settings for consistent tests."""
    # No settings to reset for extension validation
    yield


class TestXlsValidationBoundary:
    """Test pair-scoped XLS validation boundary."""

    def test_xls_with_xls_to_xlsx_operation_allowed(self, reset_extension_validator):
        """XLS allowed with operation='xls-to-xlsx'."""
        ext = file_validator_module.validate_extension("test.xls", operation="xls-to-xlsx")
        assert ext == "xls"

    def test_xls_without_operation_rejected(self, reset_extension_validator):
        """XLS rejected without operation parameter."""
        with pytest.raises(file_validator_module.FileValidationError, match="Legacy"):
            file_validator_module.validate_extension("test.xls")

    def test_xls_with_none_operation_rejected(self, reset_extension_validator):
        """XLS rejected with operation=None."""
        with pytest.raises(file_validator_module.FileValidationError, match="Legacy"):
            file_validator_module.validate_extension("test.xls", operation=None)

    def test_xls_with_unrelated_operation_rejected(self, reset_extension_validator):
        """XLS rejected with unrelated operation."""
        with pytest.raises(file_validator_module.FileValidationError, match="Legacy"):
            file_validator_module.validate_extension("test.xls", operation="pdf-merge")

    def test_doc_with_xls_to_xlsx_operation_rejected(self, reset_extension_validator):
        """DOC rejected even with operation='xls-to-xlsx'."""
        with pytest.raises(file_validator_module.FileValidationError, match="Legacy"):
            file_validator_module.validate_extension("test.doc", operation="xls-to-xlsx")

    def test_ppt_with_xls_to_xlsx_operation_rejected(self, reset_extension_validator):
        """PPT rejected even with operation='xls-to-xlsx'."""
        with pytest.raises(file_validator_module.FileValidationError, match="Legacy"):
            file_validator_module.validate_extension("test.ppt", operation="xls-to-xlsx")

    def test_xlsx_with_xls_to_xlsx_operation_allowed(self, reset_extension_validator):
        """XLSX allowed with operation='xls-to-xlsx' (normal extension)."""
        ext = file_validator_module.validate_extension("test.xlsx", operation="xls-to-xlsx")
        assert ext == "xlsx"

    def test_xlsx_without_operation_allowed(self, reset_extension_validator):
        """XLSX allowed without operation (normal extension)."""
        ext = file_validator_module.validate_extension("test.xlsx")
        assert ext == "xlsx"

    def test_pdf_without_operation_allowed(self, reset_extension_validator):
        """PDF allowed without operation (normal extension)."""
        ext = file_validator_module.validate_extension("test.pdf")
        assert ext == "pdf"


class TestXlsUploadServiceBoundary:
    """Test XLS validation through upload service."""

    def test_xls_without_operation_rejected_via_upload_service(self, monkeypatch, tmp_path):
        """XLS rejected via upload service without operation parameter."""
        monkeypatch.setattr(upload_service_module, "UPLOAD_DIR", tmp_path, raising=False)
        service = upload_service_module.UploadService()
        file = UploadFile(filename="test.xls", file=BytesIO(b"legacy xls content"))
        with pytest.raises(upload_service_module.UploadRejectedError, match="Legacy"):
            asyncio.run(service.process_upload(file))

    def test_xls_with_xls_to_xlsx_operation_passed(self, monkeypatch, tmp_path):
        """XLS with correct operation reaches next validation layer."""
        monkeypatch.setattr(upload_service_module, "UPLOAD_DIR", tmp_path, raising=False)
        service = upload_service_module.UploadService()
        file = UploadFile(filename="test.xls", file=BytesIO(b"legacy xls content"))
        # This should NOT raise a validation error at the extension level
        # It may still fail later due to content validation, but not extension
        try:
            saved_path = asyncio.run(service.process_upload(file, operation="xls-to-xlsx"))
            saved_path.unlink(missing_ok=True)
        except upload_service_module.UploadRejectedError as e:
            # If rejected, it must be a content validation error, not extension
            assert "Legacy" not in str(e)
