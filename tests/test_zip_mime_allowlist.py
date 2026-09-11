"""F5 ZIP MIME allowlist regression.

Root cause proven by the F5 MIME Investigation Gate: on Windows the browser
derives File.type for a picked .zip from the OS association data
(HKCR\\.zip "Content Type" = application/x-zip-compressed), so the real UI
upload path sent "application/x-zip-compressed" while the server allowlist
only contained "application/zip" -> HTTP 500.

This test locks in the minimal fix and, equally important, proves the reject
behavior did NOT weaken: MIME variants that were never observed from a real
browser must still be rejected for .zip.
"""

import io

import pytest

from app.utils.file_validator import FileValidationError, validate_content_type


class _StubUpload:
    """Minimal UploadFile stand-in exposing what validate_content_type reads."""

    def __init__(self, filename, content_type):
        self.filename = filename
        self.content_type = content_type
        self.file = io.BytesIO(b"PK\x03\x04")
        self.headers = {}


# Accepted: canonical value + the Windows/browser value observed in the gate.
ACCEPTED_ZIP_MIMES = [
    "application/zip",
    "application/x-zip-compressed",
]

# Still rejected: unproven legacy/vendor variants (must not be allowlisted).
REJECTED_ZIP_MIMES = [
    "application/x-zip",
    "multipart/x-zip",
    "application/x-compressed",
]


@pytest.mark.parametrize("mime", ACCEPTED_ZIP_MIMES)
def test_zip_mime_is_accepted(mime):
    stub = _StubUpload("sample.zip", mime)
    validate_content_type(stub, "zip")  # must not raise


@pytest.mark.parametrize("mime", REJECTED_ZIP_MIMES)
def test_unproven_zip_mime_is_still_rejected(mime):
    stub = _StubUpload("sample.zip", mime)
    with pytest.raises(FileValidationError):
        validate_content_type(stub, "zip")